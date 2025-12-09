"""
Logging Middleware.
Logs all incoming requests and outgoing responses with structured data.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.telemetry.logger import get_logger
from app.middlewares.correlation import get_correlation_id

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.

    Logs:
    - Request start: method, path, query params, client IP
    - Request completion: status code, duration

    All logs include the correlation ID for tracing.
    """

    # Paths to skip logging (health checks, metrics, etc.)
    SKIP_PATHS = {"/health", "/metrics", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.perf_counter()
        correlation_id = get_correlation_id()

        # Extract client IP (handle proxies)
        client_ip = self._get_client_ip(request)

        # Log request start
        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "event": "request_started",
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params) if request.query_params else None,
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Choose log level based on status code
        log_method = self._get_log_method(response.status_code)

        # Log request completion
        log_method(
            "Request completed",
            extra={
                "correlation_id": correlation_id,
                "event": "request_completed",
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP, handling proxy headers."""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # First IP in the list is the original client
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        return request.client.host if request.client else "unknown"

    def _get_log_method(self, status_code: int):
        """Get appropriate log method based on status code."""
        if status_code >= 500:
            return logger.error
        elif status_code >= 400:
            return logger.warning
        else:
            return logger.info
