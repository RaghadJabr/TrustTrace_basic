from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ...db.session import get_db
from ...ml.interfaces import FraudModelService
from ..deps import get_jofs, get_model_service

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(
    jofs=Depends(get_jofs),
    model_service: FraudModelService = Depends(get_model_service),
) -> dict[str, Any]:
    return {
        "status": "ok",
        "jofs_mode": jofs.mode,
        "traditional_model": model_service.health_check(),
    }


@router.get("/ready")
async def ready(db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # pragma: no cover - defensive
        db_status = f"error: {exc}"

    return {"status": "ok", "database": db_status}
