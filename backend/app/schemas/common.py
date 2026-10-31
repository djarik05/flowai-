"""
Common Pydantic schemas for GestureFlow AI backend.

Provides base models for API responses, errors, and pagination.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(default=None, description="Field name for validation errors")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: ErrorDetail = Field(..., description="Error details")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier for tracing")


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response format."""

    data: T = Field(..., description="Response data")
    message: Optional[str] = Field(default=None, description="Optional success message")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status (ok/degraded/offline)")
    application: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")


class APIInfo(BaseModel):
    """Basic API information."""

    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    prefix: str = Field(..., description="API URL prefix")


# Type alias for common response
ResponseData = TypeVar("ResponseData")


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid",
    }