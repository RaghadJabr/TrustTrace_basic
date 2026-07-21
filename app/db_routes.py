from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/api/database", tags=["Database"])


@router.get("/health")
def database_health(db: Session = Depends(get_db)) -> dict:
    """Confirm that FastAPI can connect to PostgreSQL."""
    try:
        row = db.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS database_user,
                    NOW() AS server_time
                """
            )
        ).mappings().one()

        return {
            "status": "connected",
            "database": row["database_name"],
            "user": row["database_user"],
            "server_time": row["server_time"],
        }
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed. Check the .env settings and PostgreSQL service.",
        ) from exc


@router.get("/traditional-assessments")
def list_traditional_assessments(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Read traditional-payment results from the database view."""
    try:
        rows = db.execute(
            text(
                """
                SELECT *
                FROM traditional_transaction_risk_view
                ORDER BY assessed_at DESC NULLS LAST
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()

        return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read traditional transaction assessments.",
        ) from exc


@router.get("/web3-assessments")
def list_web3_assessments(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Read Web3 results from the database view."""
    try:
        rows = db.execute(
            text(
                """
                SELECT *
                FROM web3_transaction_risk_view
                ORDER BY assessed_at DESC NULLS LAST
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()

        return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read Web3 transaction assessments.",
        ) from exc
