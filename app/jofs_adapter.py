from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

import httpx


class JOFSAdapter:
    """Adapter for JOFS sandbox APIs."""

    def __init__(self) -> None:
        self.mode = os.getenv("JOFS_MODE", "mock").lower()

        self.base_url = os.getenv(
            "JOFS_ACCOUNTS_BASE_URL",
            "",
        ).rstrip("/")

        self.transactions_base_url = os.getenv(
            "JOFS_TRANSACTIONS_BASE_URL",
            "",
        ).rstrip("/")

        self.beneficiaries_base_url = os.getenv(
            "JOFS_BENEFICIARIES_BASE_URL",
            "",
        ).rstrip("/")

        self.balances_base_url = os.getenv(
            "JOFS_BALANCES_BASE_URL",
            "",
        ).rstrip("/")

        self.caf_base_url = os.getenv(
            "JOFS_CAF_BASE_URL",
            "",
        ).rstrip("/")

        self.institutions_base_url = os.getenv(
            "JOFS_INSTITUTIONS_BASE_URL",
            "",
        ).rstrip("/")

        self.iban_confirmation_base_url = os.getenv(
            "JOFS_IBAN_CONFIRMATION_BASE_URL",
            "",
        ).rstrip("/")

        self.api_key = os.getenv(
            "JOFS_API_KEY",
            "",
        )

        self.customer_id = os.getenv(
            "JOFS_CUSTOMER_ID",
            "",
        )

        self.jws_signature = os.getenv(
            "JOFS_JWS_SIGNATURE",
            "",
        )

        self.financial_id = os.getenv(
            "JOFS_FINANCIAL_ID",
            "",
        )

        self.timeout = float(
            os.getenv("JOFS_TIMEOUT_SECONDS", "8")
        )

        data_path = (
            Path(__file__).parent
            / "data"
            / "demo_data.json"
        )

        self.demo_data: dict[str, Any] = json.loads(
            data_path.read_text(encoding="utf-8")
        )

    def _headers(
        self,
        interaction_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        interaction_id = interaction_id or str(uuid.uuid4())
        idempotency_key = idempotency_key or str(uuid.uuid4())

        headers = {
            "Accept": "application/json",
            "x-interactions-id": interaction_id,
            "x-idempotency-key": idempotency_key,
        }

        if self.api_key:
            headers["Authorization"] = (
                f"Bearer {self.api_key}"
            )

        if self.customer_id:
            headers["x-customer-id"] = self.customer_id

        if self.jws_signature:
            headers["x-jws-signature"] = (
                self.jws_signature
            )

        if self.financial_id:
            headers["x-financial-id"] = self.financial_id

        return headers

    async def get_accounts(
        self,
    ) -> list[dict[str, Any]]:
        if self.mode == "live":
            result = await self._live_get("/accounts")

            if not isinstance(result, list):
                raise TypeError(
                    "JOFS Accounts API did not return a list"
                )

            return result

        return self.demo_data["accounts"]

    async def get_account(
        self,
        account_id: str,
    ) -> dict[str, Any] | None:
        accounts = await self.get_accounts()

        return next(
            (
                account
                for account in accounts
                if account.get("id") == account_id
                or account.get("accountId") == account_id
            ),
            None,
        )

    async def confirm_iban_holder(
        self,
        account_type: str,
        account_id: str,
        uid_type: str,
        uid_value: str,
        auth_date: str | None = None,
    ) -> dict[str, Any]:
        account_type = account_type.strip()
        account_id = account_id.strip()
        uid_type = uid_type.strip()
        uid_value = uid_value.strip()

        if not account_type:
            raise ValueError("account_type is required")

        if not account_id:
            raise ValueError("account_id is required")

        if not uid_type:
            raise ValueError("uid_type is required")

        if not uid_value:
            raise ValueError("uid_value is required")

        if self.mode != "live":
            return {
                "status": "active",
                "matched": True,
                "accountType": account_type,
                "accountId": account_id,
                "uidType": uid_type,
            }

        if not self.iban_confirmation_base_url:
            raise RuntimeError(
                "JOFS_IBAN_CONFIRMATION_BASE_URL is required "
                "when JOFS_MODE=live"
            )

        extra_headers = {
            "accountType": account_type,
            "accountId": account_id,
            "uidType": uid_type,
            "uidValue": uid_value,
        }

        if auth_date:
            extra_headers["x-auth-date"] = auth_date

        result = await self._live_get_from_url(
            (
                f"{self.iban_confirmation_base_url}"
                "/institution/ibanConf"
            ),
            extra_headers=extra_headers,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "JOFS IBAN Confirmation API "
                "did not return an object"
            )

        return result

    async def get_balance(
        self,
        account_id: str,
    ) -> dict[str, Any]:
        if self.mode == "live":
            if not self.balances_base_url:
                raise RuntimeError(
                    "JOFS_BALANCES_BASE_URL is required "
                    "when JOFS_MODE=live"
                )

            result = await self._live_get_from_url(
                f"{self.balances_base_url}"
                f"/accounts/{account_id}/balances"
            )

            if not isinstance(result, dict):
                raise TypeError(
                    "JOFS Balances API did not return "
                    "an object"
                )

            available_balance = result.get(
                "availableBalance",
                {},
            )

            current_balance = result.get(
                "currentBalance",
                {},
            )

            return {
                "account_id": account_id,
                "available_balance": float(
                    available_balance.get(
                        "balanceAmount",
                        0,
                    )
                ),
                "current_balance": float(
                    current_balance.get(
                        "balanceAmount",
                        0,
                    )
                ),


                "credit_limit": float(
                     result.get(
                         "creditLimit",
                         result.get("creditlimit", 0),
                     )
                ),

                
                "currency": result.get(
                    "balanceCurrency",
                    "JOD",
                ),
                "raw_response": result,
            }

        account = await self.get_account(account_id)

        if not account:
            raise KeyError(
                f"Unknown account: {account_id}"
            )

        balance_value = account.get(
            "balance",
            account.get(
                "availableBalance",
                {},
            ),
        )

        if isinstance(balance_value, dict):
            balance_value = balance_value.get(
                "balanceAmount",
                0,
            )

        currency = account.get(
            "currency",
            account.get("accountCurrency", "JOD"),
        )

        return {
            "account_id": account_id,
            "available_balance": float(balance_value or 0),
            "current_balance": float(balance_value or 0),
            "credit_limit": 0.0,
            "currency": currency,
        }

    async def confirm_available_funds(
        self,
        account_id: str,
        amount: float,
        currency: str = "JOD",
    ) -> dict[str, Any]:
        if amount <= 0:
            raise ValueError(
                "Amount must be greater than zero"
            )

        if self.mode != "live":
            balance = await self.get_balance(account_id)

            available = float(
                balance.get("available_balance", 0)
            )

            return {
                "fundsAvailable": available >= amount,
                "instructionAmount": {
                    "amount": amount,
                    "currency": currency,
                },
            }

        if not self.caf_base_url:
            raise RuntimeError(
                "JOFS_CAF_BASE_URL is required "
                "when JOFS_MODE=live"
            )

        payload = {
            "instructionAmount": {
                "amount": amount,
                "currency": currency,
            }
        }

        result = await self._live_post_from_url(
            f"{self.caf_base_url}"
            f"/accounts/{account_id}/CAF",
            payload,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "JOFS CAF API did not return an object"
            )

        return result

    async def get_beneficiaries(
        self,
        account_id: str,
    ) -> list[dict[str, Any]]:
        if self.mode == "live":
            if not self.beneficiaries_base_url:
                raise RuntimeError(
                    "JOFS_BENEFICIARIES_BASE_URL "
                    "is required when JOFS_MODE=live"
                )

            result = await self._live_get_from_url(
                f"{self.beneficiaries_base_url}"
                f"/accounts/{account_id}/beneficiaries"
            )

            if not isinstance(result, list):
                raise TypeError(
                    "JOFS Beneficiaries API did not "
                    "return a list"
                )

            return result

        return [
            beneficiary
            for beneficiary in self.demo_data["beneficiaries"]
            if beneficiary.get("account_id") == account_id
        ]

    async def get_beneficiary(
        self,
        account_id: str,
        beneficiary_id: str,
    ) -> dict[str, Any] | None:
        beneficiaries = await self.get_beneficiaries(
            account_id
        )

        return next(
            (
                beneficiary
                for beneficiary in beneficiaries
                if beneficiary.get("id") == beneficiary_id
                or beneficiary.get("beneficiaryId")
                == beneficiary_id
            ),
            None,
        )

    async def get_transactions(
        self,
        account_id: str,
    ) -> list[dict[str, Any]]:
        if self.mode == "live":
            if not self.transactions_base_url:
                raise RuntimeError(
                    "JOFS_TRANSACTIONS_BASE_URL "
                    "is required when JOFS_MODE=live"
                )

            result = await self._live_get_from_url(
                f"{self.transactions_base_url}"
                f"/accounts/{account_id}/transactions"
            )

            if not isinstance(result, list):
                raise TypeError(
                    "JOFS Transactions API did not "
                    "return a list"
                )

            return result

        return self.demo_data.get(
            "transactions",
            [],
        )

    async def _live_get(
        self,
        path: str,
    ) -> Any:
        if not self.base_url:
            raise RuntimeError(
                "JOFS_ACCOUNTS_BASE_URL is required "
                "when JOFS_MODE=live"
            )

        return await self._live_get_from_url(
            f"{self.base_url}{path}"
        )

    async def _live_get_from_url(
        self,
        url: str,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                headers = self._headers()

                if extra_headers:
                    headers.update(extra_headers)

                response = await client.get(
                    url,
                    headers=headers,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"JOFS request timed out: {url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            response_text = exc.response.text

            raise RuntimeError(
                f"JOFS returned HTTP {status_code}: "
                f"{response_text}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to JOFS: {exc}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "JOFS returned invalid JSON"
            ) from exc

        if isinstance(payload, dict):
            return payload.get("data", payload)

        return payload

    async def _live_post_from_url(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.post(
                    url,
                    headers={
                        **self._headers(),
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"JOFS request timed out: {url}"
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            try:
                error_body = exc.response.json()
            except ValueError:
                error_body = exc.response.text

            raise RuntimeError(
                f"JOFS returned HTTP {status_code}: "
                f"{error_body}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Could not connect to JOFS: {exc}"
            ) from exc

        try:
            result = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "JOFS returned invalid JSON"
            ) from exc

        if isinstance(result, dict):
            return result.get("data", result)

        raise TypeError(
            "JOFS POST API did not return an object"
        )

    async def get_financial_institution(
        self,
    ) -> dict[str, Any]:
        if self.mode == "live":
            if not self.institutions_base_url:
                raise RuntimeError(
                    "JOFS_INSTITUTIONS_BASE_URL is required "
                    "when JOFS_MODE=live"
                )

            result = await self._live_get_from_url(
                f"{self.institutions_base_url}/institution"
            )

            if not isinstance(result, dict):
                raise TypeError(
                    "JOFS Financial Institutions API "
                    "did not return an object"
                )

            return result

        return {
            "institutionType": "BANK",
            "institutionIdentification": {
                "schema": "bicCode",
                "address": "JORDJOAX",
            },
        }