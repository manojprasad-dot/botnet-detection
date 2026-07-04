"""
KOVIRX — Token-bucket rate limiter.

Middleware-compatible rate limiting using in-memory state.
In production, replace with Redis-backed sliding window.
"""

import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.core.config import settings


class _TokenBucket:
    """Simple token-bucket for a single client."""

    def __init__(self, max_tokens: int, refill_seconds: float):
        self.max_tokens = max_tokens
        self.refill_rate = max_tokens / refill_seconds
        self.tokens = float(max_tokens)
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        """Try to consume one token. Returns True if allowed."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.max_tokens, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP token-bucket rate limiter.

    Configured via settings.rate_limit_requests and settings.rate_limit_window_seconds.
    """

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, _TokenBucket] = defaultdict(
            lambda: _TokenBucket(
                max_tokens=settings.rate_limit_requests,
                refill_seconds=settings.rate_limit_window_seconds,
            )
        )

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and WebSocket upgrades
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # BaseHTTPMiddleware is incompatible with WebSocket — skip /ws/ paths
        if request.url.path.startswith("/ws/"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        bucket = self._buckets[client_ip]

        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )

        return await call_next(request)
