from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from hashlib import sha256
from threading import Lock
from time import monotonic

from starlette.requests import Request

from app.core.config import Settings


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    maximum: int


class InMemoryRateLimiter:
    """Small-process rate limiter for the MVP; production can replace this with Redis."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(
        self,
        key: str,
        maximum: int,
        window_seconds: int,
        *,
        now: float | None = None,
    ) -> tuple[bool, int]:
        current = monotonic() if now is None else now
        cutoff = current - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= maximum:
                retry_after = max(1, int(window_seconds - (current - events[0])) + 1)
                return False, retry_after
            events.append(current)
            return True, 0


def identify_rate_limit_rule(request: Request, settings: Settings) -> RateLimitRule | None:
    path = request.url.path
    method = request.method.upper()
    prefix = settings.api_prefix.rstrip("/")
    exact_rules = {
        ("POST", f"{prefix}/auth/register"): RateLimitRule(
            "registration", settings.rate_limit_registration
        ),
        ("POST", f"{prefix}/auth/login"): RateLimitRule("login", settings.rate_limit_login),
        ("POST", f"{prefix}/uploads/face-image"): RateLimitRule(
            "upload", settings.rate_limit_upload
        ),
        ("POST", f"{prefix}/feedback"): RateLimitRule("feedback", settings.rate_limit_feedback),
    }
    if rule := exact_rules.get((method, path)):
        return rule
    if method == "POST" and path.endswith("/export/pdf"):
        return RateLimitRule("pdf_export", settings.rate_limit_pdf_export)
    analysis_markers = (
        "/analyze",
        "/process",
        "/evaluate",
        "/generate",
        "/regenerate",
        "/accept-warning",
    )
    if method == "POST" and any(marker in path for marker in analysis_markers):
        return RateLimitRule("analysis", settings.rate_limit_analysis)
    return None


def rate_limit_identity(request: Request) -> str:
    host = request.client.host if request.client else "unknown"
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token_fingerprint = sha256(authorization.encode("utf-8")).hexdigest()[:16]
        return f"{host}:{token_fingerprint}"
    return host
