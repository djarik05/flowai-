"""
Live dataset collection routes for GestureFlow AI backend.

Provides endpoints to start, pause, resume, and stop automated sample recording.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status

from app.schemas.dataset import (
    CollectionStartRequest,
    CollectionStatusResponse,
)
from app.services.dataset_collector import DatasetCollector
from app.services.dataset_service import DatasetService
from app.api.routes.dataset import get_gesture_service
from app.core.lifecycle import get_application_service

router = APIRouter(prefix="/collection", tags=["Collection"])

_collector: Optional[DatasetCollector] = None


def get_collector() -> DatasetCollector:
    """Get or create singleton DatasetCollector, connecting to tracking service."""
    global _collector
    if _collector is None:
        from app.api.routes.tracking import get_tracking_service
        from app.api.routes.camera import get_camera_manager

        dataset_svc = DatasetService()
        camera_manager = get_camera_manager()
        tracking_service = get_tracking_service()

        _collector = DatasetCollector(
            dataset_service=dataset_svc,
            camera_manager=camera_manager,
            tracking_service=tracking_service,
        )
    return _collector


@router.get(
    "/status",
    response_model=CollectionStatusResponse,
    summary="Get collection session status",
    description="Returns current collection progress, target samples, detection state, and FPS.",
)
async def get_collection_status() -> CollectionStatusResponse:
    """Get active collection progress and state."""
    collector = get_collector()
    return collector.get_status()


@router.post(
    "/start",
    response_model=CollectionStatusResponse,
    summary="Start dataset collection",
    description="Initiates an automated sample recording session for a specified gesture.",
)
async def start_collection(request: CollectionStartRequest) -> CollectionStatusResponse:
    """Start live dataset collection."""
    gesture_svc = get_gesture_service()
    gesture = gesture_svc.get(request.gesture_id)
    if not gesture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gesture with ID '{request.gesture_id}' not found. Please register it first.",
        )

    collector = get_collector()
    success = collector.start_collection(
        gesture_id=request.gesture_id,
        gesture_name=gesture.name,
        target_samples=request.target_samples,
        sample_interval_ms=request.sample_interval_ms,
        camera_index=request.camera_index,
    )

    if not success:
        curr_status = collector.get_status()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=curr_status.last_error or f"Collection is already in state '{curr_status.status}'. Stop existing session first.",
        )

    return collector.get_status()


@router.post(
    "/pause",
    response_model=CollectionStatusResponse,
    summary="Pause dataset collection",
    description="Temporarily suspends sample recording.",
)
async def pause_collection() -> CollectionStatusResponse:
    """Pause live collection."""
    collector = get_collector()
    success = collector.pause_collection()
    if not success:
        curr_status = collector.get_status()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause collection in state '{curr_status.status}'.",
        )
    return collector.get_status()


@router.post(
    "/resume",
    response_model=CollectionStatusResponse,
    summary="Resume dataset collection",
    description="Resumes a paused sample recording session.",
)
async def resume_collection() -> CollectionStatusResponse:
    """Resume paused collection."""
    collector = get_collector()
    success = collector.resume_collection()
    if not success:
        curr_status = collector.get_status()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume collection in state '{curr_status.status}'.",
        )
    return collector.get_status()


@router.post(
    "/stop",
    response_model=CollectionStatusResponse,
    summary="Stop dataset collection",
    description="Halts the current collection session and finalizes saved samples.",
)
async def stop_collection() -> CollectionStatusResponse:
    """Stop active collection."""
    collector = get_collector()
    collector.stop_collection()
    return collector.get_status()
