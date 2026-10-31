"""
Status routes for GestureFlow AI backend.

Provides detailed application status with component states.
"""

from fastapi import APIRouter, Request

from app.schemas.status import StatusResponse
from app.core.lifecycle import get_application_service

router = APIRouter()


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Application status",
    description="Get detailed application status including component states. Reflects actual implementation status.",
    responses={
        200: {"description": "Status retrieved successfully"},
        503: {"description": "Service not initialized"},
    },
)
async def get_status(request: Request) -> StatusResponse:
    """
    Get application status.

    Returns structured information about the backend state and all components.
    Component states explicitly reflect Phase 1 implementation status.

    Returns:
        StatusResponse with application info and component states
    """
    app_service = get_application_service()
    status_data = app_service.get_status_summary()

    return StatusResponse(**status_data)