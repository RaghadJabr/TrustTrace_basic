from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("trusttrace")


class TrustTraceAPIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Any = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def _envelope(code: str, message: str, details: Any, correlation_id: str) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "correlation_id": correlation_id,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(TrustTraceAPIError)
    async def _handle_known(request: Request, exc: TrustTraceAPIError) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.warning(
            "trusttrace_api_error",
            extra={"code": exc.code, "path": request.url.path, "correlation_id": correlation_id},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details, correlation_id),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        correlation_id = str(uuid.uuid4())
        logger.exception(
            "trusttrace_unhandled_error",
            extra={"path": request.url.path, "correlation_id": correlation_id},
        )
        return JSONResponse(
            status_code=500,
            content=_envelope(
                "INTERNAL_ERROR",
                "The request could not be completed.",
                None,
                correlation_id,
            ),
        )
