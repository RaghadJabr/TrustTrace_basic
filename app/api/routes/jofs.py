from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ...integrations.open_finance.provider import JOFSAdapter
from ...schemas import FundsConfirmationRequest, IBANConfirmationRequest
from ..deps import get_jofs

router = APIRouter(prefix="/api/jofs", tags=["jofs"])


@router.get("/institution")
async def institution(jofs: JOFSAdapter = Depends(get_jofs)) -> dict[str, Any]:
    try:
        return await jofs.get_financial_institution()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Financial Institution error: {exc}") from exc


@router.get("/accounts")
async def accounts(jofs: JOFSAdapter = Depends(get_jofs)) -> list[dict[str, Any]]:
    try:
        return await jofs.get_accounts()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Accounts error: {exc}") from exc


@router.get("/accounts/{account_id}")
async def account(account_id: str, jofs: JOFSAdapter = Depends(get_jofs)) -> dict[str, Any]:
    try:
        result = await jofs.get_account(account_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Account error: {exc}") from exc


@router.get("/accounts/{account_id}/balance")
async def balance(account_id: str, jofs: JOFSAdapter = Depends(get_jofs)) -> dict[str, Any]:
    try:
        return await jofs.get_balance(account_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Balances error: {exc}") from exc


@router.get("/accounts/{account_id}/beneficiaries")
async def beneficiaries(account_id: str, jofs: JOFSAdapter = Depends(get_jofs)) -> list[dict[str, Any]]:
    try:
        return await jofs.get_beneficiaries(account_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Beneficiaries error: {exc}") from exc


@router.get("/accounts/{account_id}/beneficiaries/{beneficiary_id}")
async def beneficiary(
    account_id: str, beneficiary_id: str, jofs: JOFSAdapter = Depends(get_jofs)
) -> dict[str, Any]:
    try:
        result = await jofs.get_beneficiary(account_id=account_id, beneficiary_id=beneficiary_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Beneficiary {beneficiary_id} not found for account {account_id}",
            )
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Beneficiary error: {exc}") from exc


@router.get("/accounts/{account_id}/transactions")
async def transactions(account_id: str, jofs: JOFSAdapter = Depends(get_jofs)) -> list[dict[str, Any]]:
    try:
        return await jofs.get_transactions(account_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS Transactions error: {exc}") from exc


@router.post("/accounts/{account_id}/confirm-funds")
async def confirm_funds(
    account_id: str, request: FundsConfirmationRequest, jofs: JOFSAdapter = Depends(get_jofs)
) -> dict[str, Any]:
    try:
        return await jofs.confirm_available_funds(
            account_id=account_id, amount=request.amount, currency=request.currency
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"JOFS CAF error: {exc}") from exc


@router.post("/iban-confirmation")
async def iban_confirmation(
    request: IBANConfirmationRequest, jofs: JOFSAdapter = Depends(get_jofs)
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"JOFS IBAN Confirmation error: {type(exc).__name__}: {exc}"
        ) from exc
