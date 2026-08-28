from __future__ import annotations

import json
import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import Settings
from app.core.rate_limit import (
    InMemoryRateLimiter,
    identify_rate_limit_rule,
    rate_limit_identity,
)

logger = logging.getLogger("dermascan.requests")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _request_id(request: Request) -> str:
    candidate = request.headers.get("x-request-id", "")
    if REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid4().hex


def _security_headers(response, settings: Settings) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), geolocation=(), microphone=()"
    response.headers["X-Frame-Options"] = "DENY"
    if settings.enable_hsts:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


def register_operational_middleware(app, settings: Settings) -> None:
    app.state.rate_limiter = InMemoryRateLimiter()
    app.state.operational_metrics = {
        "request_count": 0,
        "error_count": 0,
        "duration_ms_total": 0.0,
        "upload_rejection_count": 0,
        "analysis_failure_count": 0,
        "pdf_export_failure_count": 0,
    }

    @app.middleware("http")
    async def observe_request(request: Request, call_next):
        request_id = _request_id(request)
        request.state.request_id = request_id
        started = perf_counter()
        rule = identify_rate_limit_rule(request, settings)
        if settings.rate_limit_enabled and not settings.is_testing and rule is not None:
            identity = rate_limit_identity(request)
            allowed, retry_after = app.state.rate_limiter.allow(
                f"{rule.name}:{identity}",
                rule.maximum,
                settings.rate_limit_window_seconds,
            )
            if not allowed:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests. Please wait before trying again.",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "request_id": request_id,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
                _security_headers(response, settings)
                return response

        response = await call_next(request)
        duration_ms = round((perf_counter() - started) * 1000, 2)
        metrics = app.state.operational_metrics
        metrics["request_count"] += 1
        metrics["duration_ms_total"] += duration_ms
        if response.status_code >= 400:
            metrics["error_count"] += 1
            path = request.url.path
            if path.endswith("/face-image"):
                metrics["upload_rejection_count"] += 1
            if any(part in path for part in ("/analyze", "/process", "/generate")):
                metrics["analysis_failure_count"] += 1
            if path.endswith("/export/pdf"):
                metrics["pdf_export_failure_count"] += 1
        response.headers["X-Request-ID"] = request_id
        _security_headers(response, settings)
        logger.info(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "route": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
                separators=(",", ":"),
            )
        )
        return response
