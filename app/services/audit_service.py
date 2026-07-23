from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from ..models.orm import AuditLog


def record(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    correlation_id: uuid.UUID,
    details: dict[str, Any],
) -> AuditLog:
    log = AuditLog(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=correlation_id,
        details=details,
    )
    db.add(log)
    return log
