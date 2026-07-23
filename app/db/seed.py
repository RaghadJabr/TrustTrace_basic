"""Demo seed data.

Backdates a demo account with a small history of ordinary "Noon Jordan"
purchases so avg_amount_deviation_sigma and account_age_days -- both real
features the LightGBM model consumes -- have a meaningful baseline the very
first time someone runs the "safe" vs "suspicious" scenarios, instead of
scoring a brand-new, zero-history account both times.

Idempotent: does nothing if the demo account already exists. Run directly
with `python -m app.db.seed`, or it is called once automatically on startup
in app/main.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.orm import Account, Customer, Merchant, Transaction

DEMO_ACCOUNT_REF = "ACC-1001"
DEMO_MERCHANT_DOMAIN = "www.noon.com"


def seed_demo_data(db: Session) -> bool:
    existing = db.scalar(select(Account).where(Account.external_account_id == DEMO_ACCOUNT_REF))
    if existing is not None:
        return False

    now = datetime.now(timezone.utc)

    customer = Customer(external_customer_ref=DEMO_ACCOUNT_REF, created_at=now - timedelta(days=410))
    db.add(customer)
    db.flush()

    account = Account(
        customer_id=customer.id,
        external_account_id=DEMO_ACCOUNT_REF,
        available_balance=2450.75,
        currency="JOD",
        masked_iban="JO94 **** **** 1932",
        created_at=now - timedelta(days=410),
    )
    db.add(account)
    db.flush()

    merchant = Merchant(
        merchant_name="Noon Jordan",
        merchant_domain=DEMO_MERCHANT_DOMAIN,
        category="retail",
        reputation_score=85,
        verified=True,
    )
    db.add(merchant)
    db.flush()

    baseline_amounts = [45.0, 62.5, 38.0, 71.0, 55.5, 48.0]
    for offset, amount in enumerate(baseline_amounts, start=1):
        db.add(
            Transaction(
                account_id=account.id,
                merchant_id=merchant.id,
                amount=amount,
                currency="JOD",
                city="Amman",
                channel="card_checkout",
                status="settled",
                created_at=now - timedelta(days=60 - offset * 7),
            )
        )

    db.commit()
    return True


if __name__ == "__main__":
    from .session import SessionLocal

    session = SessionLocal()
    try:
        seeded = seed_demo_data(session)
        print("Seeded demo data." if seeded else "Demo data already present; nothing to do.")
    finally:
        session.close()
