"""
Gesture routes for GestureFlow AI backend.

Provides endpoints for gesture CRUD, registration, and sample counts.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.gesture import (
    GestureCreate,
    GestureListResponse,
    GestureResponse,
    GestureUpdate,
)
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService

router = APIRouter(prefix="/gestures", tags=["Gestures"])

_gesture_service: Optional[GestureService] = None
_dataset_service: Optional[DatasetService] = None


def get_gesture_service() -> GestureService:
    """Get or initialize the gesture service."""
    global _gesture_service
    if _gesture_service is None:
        _gesture_service = GestureService()
    return _gesture_service


def get_dataset_service() -> DatasetService:
    """Get or initialize the dataset service."""
    global _dataset_service
    if _dataset_service is None:
        _dataset_service = DatasetService()
    return _dataset_service


@router.get(
    "",
    response_model=GestureListResponse,
    summary="List all registered gestures",
    description="Returns all gestures in the registry with dynamic sample counts.",
)
async def list_gestures() -> GestureListResponse:
    """Get all registered gestures with sample counts."""
    gesture_svc = get_gesture_service()
    dataset_svc = get_dataset_service()

    counts = dataset_svc.get_sample_counts_by_gesture()
    gestures = gesture_svc.get_all(sample_counts=counts)

    return GestureListResponse(
        gestures=gestures,
        total=len(gestures),
    )


@router.post(
    "",
    response_model=GestureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom gesture",
    description="Registers a new custom gesture in the system.",
)
async def create_gesture(data: GestureCreate) -> GestureResponse:
    """Create a new custom gesture."""
    gesture_svc = get_gesture_service()
    try:
        new_gesture = gesture_svc.create(data)
        return new_gesture
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    "/{gesture_id}",
    response_model=GestureResponse,
    summary="Get gesture details",
    description="Returns details and sample count for a specific gesture ID.",
)
async def get_gesture(gesture_id: str) -> GestureResponse:
    """Get details for a specific gesture."""
    gesture_svc = get_gesture_service()
    dataset_svc = get_dataset_service()

    counts = dataset_svc.get_sample_counts_by_gesture()
    sample_count = counts.get(gesture_id, 0)

    gesture = gesture_svc.get(gesture_id, sample_count=sample_count)
    if not gesture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gesture with ID '{gesture_id}' not found.",
        )
    return gesture


@router.put(
    "/{gesture_id}",
    response_model=GestureResponse,
    summary="Update gesture definition",
    description="Modifies an existing gesture's name, description, or action.",
)
async def update_gesture(gesture_id: str, updates: GestureUpdate) -> GestureResponse:
    """Update an existing gesture."""
    gesture_svc = get_gesture_service()
    dataset_svc = get_dataset_service()

    counts = dataset_svc.get_sample_counts_by_gesture()
    sample_count = counts.get(gesture_id, 0)

    updated = gesture_svc.update(gesture_id, updates, sample_count=sample_count)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gesture with ID '{gesture_id}' not found.",
        )
    return updated


@router.delete(
    "/{gesture_id}",
    summary="Delete a gesture",
    description="Removes a gesture from the registry and optionally its sample files.",
)
async def delete_gesture(
    gesture_id: str,
    delete_samples: bool = Query(default=False, description="Whether to also delete all collected samples"),
) -> dict:
    """Delete a gesture."""
    gesture_svc = get_gesture_service()
    dataset_svc = get_dataset_service()

    gesture = gesture_svc.get(gesture_id)
    if not gesture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gesture with ID '{gesture_id}' not found.",
        )

    deleted_samples_count = 0
    if delete_samples:
        deleted_samples_count = dataset_svc.delete_gesture_samples(gesture_id)

    success = gesture_svc.delete(gesture_id)
    return {
        "success": success,
        "message": f"Gesture '{gesture_id}' deleted successfully.",
        "samples_deleted": deleted_samples_count,
    }
