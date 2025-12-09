"""
Standard API Response Formatters.

Provides consistent response formats across all endpoints.
"""
from typing import Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    data: Any


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str
    message: str
    correlation_id: Optional[str] = None
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: ErrorDetail


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel):
    """Standard paginated response."""
    success: bool = True
    data: List[Any]
    pagination: PaginationInfo


def success_response(data: Any) -> dict:
    """
    Format a successful response.

    Args:
        data: Response data

    Returns:
        Formatted response dict
    """
    return {
        "success": True,
        "data": data,
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> dict:
    """
    Format a paginated response.

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        page_size: Items per page

    Returns:
        Formatted paginated response dict
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        }
    }


def error_response(
    code: str,
    message: str,
    correlation_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> dict:
    """
    Format an error response.

    Args:
        code: Error code
        message: Human-readable error message
        correlation_id: Request correlation ID
        details: Additional error details

    Returns:
        Formatted error response dict
    """
    response = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        }
    }

    if correlation_id:
        response["error"]["correlation_id"] = correlation_id

    if details:
        response["error"]["details"] = details

    return response


def created_response(data: Any, message: str = "Created successfully") -> dict:
    """
    Format a 201 Created response.

    Args:
        data: Created resource data
        message: Success message

    Returns:
        Formatted response dict
    """
    return {
        "success": True,
        "message": message,
        "data": data,
    }


def deleted_response(message: str = "Deleted successfully") -> dict:
    """
    Format a delete success response.

    Args:
        message: Success message

    Returns:
        Formatted response dict
    """
    return {
        "success": True,
        "message": message,
    }
