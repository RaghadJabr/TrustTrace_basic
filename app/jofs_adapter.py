from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import httpx


class JOFSAdapter:
    """Small adapter around JOFS.

    The hackathon build defaults to mock mode because the public document shows
    resources such as Accounts, Balances and Beneficiaries, but credentials and
    exact production URLs must be supplied by the organizers.
    """

    def __init__(self) -> None:
        self.mode = os.getenv("JOFS_MODE", "mock").lower()
        self.base_url = os.getenv("JOFS_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("JOFS_API_KEY", "")
        self.timeout = float(os.getenv("JOFS_TIMEOUT_SECONDS", "8"))
        data_path = Path(__file__).parent / "data" / "demo_data.json"
        self.demo_data: dict[str, Any] = json.loads(data_path.read_text(encoding="utf-8"))

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_accounts(self) -> list[dict[str, Any]]:
        if self.mode == "live":
            return await self._live_get("/accounts")
        return self.demo_data["accounts"]

    async def get_account(self, account_id: str) -> dict[str, Any] | None:
        accounts = await self.get_accounts()
        return next((a for a in accounts if a.get("id") == account_id), None)

    async def get_balance(self, account_id: str) -> dict[str, Any]:
        if self.mode == "live":
            return await self._live_get(f"/accounts/{account_id}/balances")
        account = await self.get_account(account_id)
        if not account:
            raise KeyError(f"Unknown account: {account_id}")
        return {
            "account_id": account_id,
            "available_balance": account["balance"],
            "currency": account["currency"],
        }

    async def get_beneficiaries(self, account_id: str) -> list[dict[str, Any]]:
        if self.mode == "live":
            return await self._live_get(f"/accounts/{account_id}/beneficiaries")
        return [
            b for b in self.demo_data["beneficiaries"] if b.get("account_id") == account_id
        ]

    async def get_beneficiary(self, account_id: str, beneficiary_id: str) -> dict[str, Any] | None:
        beneficiaries = await self.get_beneficiaries(account_id)
        return next((b for b in beneficiaries if b.get("id") == beneficiary_id), None)

    async def _live_get(self, path: str) -> Any:
        if not self.base_url:
            raise RuntimeError("JOFS_BASE_URL is required when JOFS_MODE=live")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=self._headers(),
            )
            response.raise_for_status()
            payload = response.json()
            # Adapt this mapping after inspecting the exact JOFS sandbox response.
            return payload.get("data", payload)
