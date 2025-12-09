"""
Correlation ID Middleware.
Assigns a unique ID to each request for distributed tracing and debugging.
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable accessible throughout the request lifecycle
# This allows any part of the code to access the correlation ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle X-Correlation-ID header.

    - Extracts correlation ID from incoming request header
    - Generates new UUID if not provided
    - Makes it available via context variable (correlation_id_var)
    - Adds correlation ID to response headers

    Usage:
        # In any part of your code:
        from app.middlewares.correlation import get_correlation_id
        correlation_id = get_correlation_id()
    """

    HEADER_NAME = "X-Correlation-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get from incoming header or generate new
        correlation_id = request.headers.get(
            self.HEADER_NAME,
            str(uuid.uuid4())
        )

        # Store in context variable (accessible anywhere in request lifecycle)
        correlation_id_var.set(correlation_id)

        # Process the request
        response = await call_next(request)

        # Add to response headers for client tracking
        response.headers[self.HEADER_NAME] = correlation_id

        return response


def get_correlation_id() -> str:
    """
    Get the current request's correlation ID.

    Returns:
        The correlation ID string, or empty string if not in a request context.

    Example:
        from app.middlewares.correlation import get_correlation_id

        def some_function():
            correlation_id = get_correlation_id()
            logger.info(f"[{correlation_id}] Processing...")
    """
    return correlation_id_var.get()
