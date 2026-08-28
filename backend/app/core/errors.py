from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "ACCESS_FORBIDDEN",
    404: "RESOURCE_NOT_FOUND",
    409: "RESOURCE_CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "REQUEST_VALIDATION_FAILED",
    429: "RATE_LIMIT_EXCEEDED",
    503: "SERVICE_UNAVAILABLE",
}


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _body(request: Request, detail: Any, status_code: int) -> dict[str, Any]:
    body: dict[str, Any] = {
        "detail": detail,
        "code": STATUS_CODES.get(status_code, "REQUEST_FAILED"),
    }
    if request_id := _request_id(request):
        body["request_id"] = request_id
    return body


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_body(request, exc.detail, exc.status_code),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(_body(request, exc.errors(), 422)),
    )


async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled request failure request_id=%s error_code=INTERNAL_SERVER_ERROR",
        _request_id(request),
    )
    body = _body(
        request,
        "The requested resource could not be processed.",
        500,
    )
    body["code"] = "INTERNAL_SERVER_ERROR"
    return JSONResponse(status_code=500, content=body)
