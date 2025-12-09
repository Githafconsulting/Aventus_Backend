"""
Timing Middleware.
Adds response time header to all responses for performance monitoring.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds X-Response-Time header to all responses.

    This is useful for:
    - Client-side performance monitoring
    - Load balancer health checks
    - API performance debugging

    The header value is in milliseconds (e.g., "123.45ms").
    """

    HEADER_NAME = "X-Response-Time"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration in milliseconds
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add timing header
        response.headers[self.HEADER_NAME] = f"{duration_ms:.2f}ms"

        return response
