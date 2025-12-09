"""
Error Handling Middleware.
Catches all exceptions and returns consistent JSON error responses.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from app.telemetry.logger import get_logger
from app.middlewares.correlation import get_correlation_id
from app.exceptions.base import BaseAppException
from app.exceptions.auth import AuthenticationError, AuthorizationError
from app.exceptions.validation import ValidationError

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.

    Features:
    - Catches all exceptions
    - Returns consistent JSON error response format
    - Logs errors with full context
    - Never exposes stack traces to clients (security)
    - Includes correlation ID in error responses

    Error Response Format:
    {
        "success": false,
        "error": {
            "code": "error_code",
            "message": "Human readable message",
            "correlation_id": "uuid",
            "details": {}  // Optional
        }
    }
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except AuthenticationError as e:
            return self._create_error_response(
                status_code=401,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )

        except AuthorizationError as e:
            return self._create_error_response(
                status_code=403,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )

        except ValidationError as e:
            return self._create_error_response(
                status_code=422,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )

        except PydanticValidationError as e:
            return self._create_error_response(
                status_code=422,
                error_code="validation_error",
                message="Invalid request data",
                details={"errors": e.errors()},
            )

        except BaseAppException as e:
            # Log application exceptions
            logger.warning(
                f"Application exception: {e.message}",
                extra={
                    "correlation_id": get_correlation_id(),
                    "error_code": e.error_code,
                    "path": request.url.path,
                }
            )
            return self._create_error_response(
                status_code=e.status_code,
                error_code=e.error_code,
                message=e.message,
                details=e.details,
            )

        except Exception as e:
            # Log unexpected exceptions with full traceback
            logger.exception(
                "Unhandled exception",
                extra={
                    "correlation_id": get_correlation_id(),
                    "path": request.url.path,
                    "method": request.method,
                    "error_type": type(e).__name__,
                }
            )

            # Return safe message to client (never expose internal details)
            return self._create_error_response(
                status_code=500,
                error_code="internal_error",
                message="An unexpected error occurred. Please try again later.",
            )

    def _create_error_response(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: dict = None,
    ) -> JSONResponse:
        """Create standardized error response."""
        content = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "correlation_id": get_correlation_id(),
            }
        }

        if details:
            content["error"]["details"] = details

        return JSONResponse(
            status_code=status_code,
            content=content,
        )
