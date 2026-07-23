from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .jofs_adapter import JOFSAdapter
from .models import (
    FundsConfirmationRequest,
    IBANConfirmationRequest,
    RiskAssessment,
    TraditionalRiskRequest,
    Web3RiskRequest,
)
from .risk_engine import RiskEngine


load_dotenv(override=True)

app = FastAPI(
    title="TrustTrace Prototype API",
    version="0.1.0",
    description=(
        "Explainable pre-authorization fraud assessment "
        "for traditional and Web3 payments."
    ),
)

jofs = JOFSAdapter()
risk_engine = RiskEngine(jofs)

static_dir = Path(__file__).parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=static_dir),
    name="static",
)


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "jofs_mode": jofs.mode,
        "accounts_base_url": jofs.base_url,
        "transactions_base_url": jofs.transactions_base_url,
        "beneficiaries_base_url": jofs.beneficiaries_base_url,
        "balances_base_url": jofs.balances_base_url,
        "caf_base_url": jofs.caf_base_url,
        "institutions_base_url": jofs.institutions_base_url,
    }


@app.get("/api/jofs/institution")
async def institution() -> dict[str, Any]:
    try:
        return await jofs.get_financial_institution()

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Financial Institution error: {exc}",
        ) from exc

@app.get("/api/jofs/accounts")
async def accounts() -> list[dict[str, Any]]:
    try:
        return await jofs.get_accounts()

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Accounts error: {exc}",
        ) from exc


@app.get("/api/jofs/accounts/{account_id}")
async def account(
    account_id: str,
) -> dict[str, Any]:
    try:
        result = await jofs.get_account(account_id)

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Account not found: {account_id}",
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Account error: {exc}",
        ) from exc


@app.get("/api/jofs/accounts/{account_id}/balance")
async def balance(
    account_id: str,
) -> dict[str, Any]:
    try:
        return await jofs.get_balance(account_id)

    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Balances error: {exc}",
        ) from exc


@app.get("/api/jofs/accounts/{account_id}/beneficiaries")
async def beneficiaries(
    account_id: str,
) -> list[dict[str, Any]]:
    try:
        return await jofs.get_beneficiaries(account_id)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Beneficiaries error: {exc}",
        ) from exc


@app.get(
    "/api/jofs/accounts/{account_id}/beneficiaries/"
    "{beneficiary_id}"
)
async def beneficiary(
    account_id: str,
    beneficiary_id: str,
) -> dict[str, Any]:
    try:
        result = await jofs.get_beneficiary(
            account_id=account_id,
            beneficiary_id=beneficiary_id,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Beneficiary {beneficiary_id} "
                    f"not found for account {account_id}"
                ),
            )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Beneficiary error: {exc}",
        ) from exc


@app.get("/api/jofs/accounts/{account_id}/transactions")
async def transactions(
    account_id: str,
) -> list[dict[str, Any]]:
    try:
        return await jofs.get_transactions(account_id)

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS Transactions error: {exc}",
        ) from exc


@app.post(
    "/api/jofs/accounts/{account_id}/confirm-funds"
)
async def confirm_funds(
    account_id: str,
    request: FundsConfirmationRequest,
) -> dict[str, Any]:
    try:
        return await jofs.confirm_available_funds(
            account_id=account_id,
            amount=request.amount,
            currency=request.currency,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"JOFS CAF error: {exc}",
        ) from exc


@app.post(
    "/api/risk/traditional",
    response_model=RiskAssessment,
)
async def assess_traditional(
    request: TraditionalRiskRequest,
) -> RiskAssessment:
    try:
        return await risk_engine.assess_traditional(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Risk assessment error: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

@app.post("/api/jofs/iban-confirmation")
async def iban_confirmation(
    request: IBANConfirmationRequest,
) -> dict[str, Any]:
    try:
        return await jofs.confirm_iban_holder(
            account_type=request.account_type,
            account_id=request.account_id,
            uid_type=request.uid_type,
            uid_value=request.uid_value,
            auth_date=request.auth_date,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "JOFS IBAN Confirmation error: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@app.post(
    "/api/risk/web3",
    response_model=RiskAssessment,
)
async def assess_web3(
    request: Web3RiskRequest,
) -> RiskAssessment:
    try:
        return await risk_engine.assess_web3(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Web3 risk assessment error: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@app.get("/api/demo/scenarios")
async def scenarios() -> dict[str, Any]:
    return {
        "traditional": {
            "safe": {
                "account_id": "1001",
                "beneficiary_id": "2",
                "amount": 50,
                "currency": "JOD",
                "merchant": "Noon Jordan",
                "domain": "www.noon.com",
                "device_id": "KNOWN-DEVICE",
                "location": "Amman",
                "rapid_attempts": 0,
            },
            "suspicious": {
                "account_id": "1001",
                "beneficiary_id": "1",
                "amount": 6000,
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
                "wallet_address": (
                    "0xLEEN000000000000000000000000000000000001"
                ),
                "contract_address": (
                    "0xSAFE000000000000000000000000000000000001"
                ),
                "network": "ethereum",
                "action": "token_approval",
                "token_symbol": "USDT",
                "approval_limit": "limited",
                "wallet_scam_reports": 0,
                "suspicious_network": False,
            },
            "suspicious": {
                "wallet_address": (
                    "0xLEEN000000000000000000000000000000000001"
                ),
                "contract_address": (
                    "0xBAD0000000000000000000000000000000000777"
                ),
                "network": "ethereum",
                "action": "token_approval",
                "token_symbol": "USDT",
                "approval_limit": "unlimited",
                "wallet_scam_reports": 5,
                "suspicious_network": True,
            },
        },
    }
