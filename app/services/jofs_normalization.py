"""Normalizes raw JOFS responses into internal shapes.

JOFSAdapter's mock mode returns the shape documented in app/data/demo_data.json;
live mode (per the sandbox docs, unverified against a real endpoint -- see
README) returns something closer to Berlin-Group/NextGenPSD2 field names
(transactionAmount.amount, bookingDate, beneficiaryId, ...). This module is
the single place that knows both shapes, so the rest of the pipeline
(feature_service, assessment_service) only ever sees one normalized shape
regardless of JOFS_MODE.

Nothing here invents data: a field that genuinely isn't present in the JOFS
response comes back as None and must be handled by an explicit, documented
fallback upstream -- never silently guessed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class NormalizedAccount:
    external_account_id: str
    display_name: str | None
    masked_iban: str | None
    currency: str | None


@dataclass
class NormalizedBeneficiary:
    external_beneficiary_id: str
    name: str | None
    verified: bool | None


@dataclass
class NormalizedTransaction:
    external_transaction_id: str | None
    amount: float
    currency: str | None
    timestamp: datetime | None
    transaction_type: str | None


def normalize_account(raw: dict[str, Any]) -> NormalizedAccount:
    external_id = raw.get("id") or raw.get("accountId") or raw.get("resourceId")
    return NormalizedAccount(
        external_account_id=str(external_id) if external_id is not None else "",
        display_name=raw.get("name") or raw.get("ownerName"),
        masked_iban=raw.get("masked_iban") or raw.get("iban") or raw.get("maskedPan"),
        currency=raw.get("currency") or raw.get("accountCurrency"),
    )


def normalize_beneficiary(raw: dict[str, Any] | None) -> NormalizedBeneficiary | None:
    if raw is None:
        return None
    external_id = raw.get("id") or raw.get("beneficiaryId")
    if external_id is None:
        return None
    return NormalizedBeneficiary(
        external_beneficiary_id=str(external_id),
        name=raw.get("name") or raw.get("creditorName"),
        # "verified" is a mock-only convenience field; the real JOFS beneficiary
        # resource has no such attribute, so this is None (unknown) in live mode
        # rather than defaulted to True/False.
        verified=raw.get("verified"),
    )


def _parse_timestamp(raw: dict[str, Any]) -> datetime | None:
    value = raw.get("date") or raw.get("bookingDate") or raw.get("valueDate")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def normalize_transaction(raw: dict[str, Any]) -> NormalizedTransaction | None:
    if "amount" in raw:
        amount = raw.get("amount")
        currency = raw.get("currency")
    else:
        amount_block = raw.get("transactionAmount") or {}
        amount = amount_block.get("amount")
        currency = amount_block.get("currency")

    if amount is None:
        return None

    external_id = raw.get("id") or raw.get("transactionId")

    return NormalizedTransaction(
        external_transaction_id=str(external_id) if external_id is not None else None,
        amount=float(amount),
        currency=currency,
        timestamp=_parse_timestamp(raw),
        transaction_type=raw.get("transaction_type") or raw.get("transactionType"),
    )


def normalize_transactions(raw_list: list[dict[str, Any]]) -> list[NormalizedTransaction]:
    normalized = [normalize_transaction(item) for item in raw_list]
    return [item for item in normalized if item is not None]
