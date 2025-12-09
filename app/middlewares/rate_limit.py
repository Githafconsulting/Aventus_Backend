"""
Rate Limiting Middleware.
Prevents abuse by limiting requests per client IP.
"""
import time
from collections import defaultdict
from typing import Dict, List, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.middlewares.correlation import get_correlation_id
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter based on client IP.

    Features:
    - Configurable requests per minute
    - Per-IP tracking
    - Automatic cleanup of old entries
    - Returns 429 Too Many Requests when limit exceeded

    Note: For production with multiple instances, use Redis-based rate limiting.

    Usage:
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
    """

    # Paths to exclude from rate limiting
    EXCLUDE_PATHS = {"/health", "/metrics", "/docs", "/redoc", "/openapi.json"}

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: Optional[int] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            app: The ASGI application
            requests_per_minute: Maximum requests allowed per minute per IP
            burst_limit: Optional burst limit (defaults to requests_per_minute)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit or requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if request.url.path in self.EXCLUDE_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        # Periodic cleanup of old entries (every 60 seconds)
        if now - self._last_cleanup > 60:
            self._cleanup_old_entries(now)
            self._last_cleanup = now

        # Clean old requests for this IP
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if now - t < 60  # Keep requests from last minute
        ]

        # Check if limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "correlation_id": get_correlation_id(),
                    "client_ip": client_ip,
                    "requests_count": len(self.requests[client_ip]),
                    "limit": self.requests_per_minute,
                    "path": request.url.path,
                }
            )

            # Calculate retry-after
            oldest_request = min(self.requests[client_ip])
            retry_after = int(60 - (now - oldest_request))

            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Too many requests. Please slow down.",
                        "correlation_id": get_correlation_id(),
                        "retry_after": max(1, retry_after),
                    }
                },
                headers={"Retry-After": str(max(1, retry_after))}
            )

        # Record this request
        self.requests[client_ip].append(now)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP, handling proxy headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _cleanup_old_entries(self, now: float) -> None:
        """Remove IPs with no recent requests to free memory."""
        empty_ips = [
            ip for ip, timestamps in self.requests.items()
            if not timestamps or all(now - t > 60 for t in timestamps)
        ]
        for ip in empty_ips:
            del self.requests[ip]
