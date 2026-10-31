"""
Exception handlers for GestureFlow AI backend.

Provides consistent error responses and logging for all exception types.
"""

import logging
import traceback
from typing import Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when application configuration is invalid."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ApplicationStartupError(Exception):
    """Raised when application fails to start."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.cause = cause


async def configuration_error_handler(request: Request, exc: ConfigurationError) -> JSONResponse:
    """Handle configuration errors."""
    logger.error("Configuration error: %s", exc.message, extra={"details": exc.details})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="CONFIGURATION_ERROR",
                message="Application configuration is invalid",
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


async def application_startup_error_handler(request: Request, exc: ApplicationStartupError) -> JSONResponse:
    """Handle application startup errors."""
    logger.critical(
        "Application startup failed: %s",
        exc.message,
        exc_info=exc.cause,
        extra={"cause": str(exc.cause) if exc.cause else None},
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=ErrorResponse(
            error=ErrorDetail(
                code="STARTUP_ERROR",
                message="Application failed to start",
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    # Extract field name from error location
    field_name = None
    if first_error.get("loc"):
        loc = first_error["loc"]
        if len(loc) > 1:
            field_name = ".".join(str(x) for x in loc[1:])
        elif len(loc) == 1:
            field_name = str(loc[0])

    logger.warning(
        "Request validation error: %s",
        first_error.get("msg", "Invalid request"),
        extra={
            "field": field_name,
            "errors": errors,
            "path": str(request.url),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=first_error.get("msg", "Invalid request data"),
                field=field_name,
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


async def pydantic_validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors()
    first_error = errors[0] if errors else {}

    field_name = None
    if first_error.get("loc"):
        field_name = ".".join(str(x) for x in first_error["loc"])

    logger.warning(
        "Pydantic validation error: %s",
        first_error.get("msg", "Validation failed"),
        extra={"field": field_name, "errors": errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message=first_error.get("msg", "Validation failed"),
                field=field_name,
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(
        "HTTP exception: %d - %s",
        exc.status_code,
        exc.detail,
        extra={"path": str(request.url), "status_code": exc.status_code},
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    # Log full traceback internally but don't expose to client
    logger.error(
        "Unhandled exception: %s",
        str(exc),
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc(),
        },
    )

    # In production, don't expose internal error details
    is_production = request.app.state.settings.environment == "production"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred" if is_production else str(exc),
            ),
            request_id=getattr(request.state, "request_id", None),
        ).model_dump(),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    app.add_exception_handler(ApplicationStartupError, application_startup_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")