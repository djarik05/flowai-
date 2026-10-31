"""
Health check routes for GestureFlow AI backend.

Provides lightweight endpoint to verify API responsiveness.
"""

from fastapi import APIRouter, Request

from app.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verify that the API process is responding. Does not verify camera, model, or controller status.",
    responses={
        200: {"description": "API is healthy"},
        503: {"description": "Service unavailable"},
    },
)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Returns basic health status without verifying external dependencies.
    This endpoint should be lightweight and fast.

    Returns:
        HealthResponse with status, application name, and version
    """
    return HealthResponse(
        status="ok",
        application=settings.app_name,
        version=settings.app_version,
    )