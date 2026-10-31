"""
Temporal Gesture Recognition and Sequence Dataset routes for GestureFlow AI backend.

Endpoints:
- GET  /api/v1/temporal/status
- GET  /api/v1/temporal/gestures
- GET  /api/v1/temporal/events
- POST /api/v1/temporal/reset
- POST /api/v1/temporal/dataset/start
- POST /api/v1/temporal/dataset/commit
- POST /api/v1/temporal/dataset/stop
- GET  /api/v1/temporal/dataset/status
- GET  /api/v1/temporal/dataset/stats
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.temporal import (
    TemporalCollectionStatus,
    TemporalEngineStatusResponse,
    TemporalGestureDefinition,
    TemporalGestureEvent,
    TemporalSequenceSample,
)
from app.services.temporal import (
    TEMPORAL_GESTURE_CATALOG,
    get_temporal_dataset_service,
    get_temporal_engine,
)

router = APIRouter(prefix="/temporal", tags=["Temporal Gesture Recognition"])


@router.get(
    "/status",
    response_model=TemporalEngineStatusResponse,
    summary="Get temporal gesture engine status",
    description="Returns current tracking state, active buffers, kinematics telemetry, and recent events.",
)
async def get_temporal_status() -> TemporalEngineStatusResponse:
    engine = get_temporal_engine()
    return engine.get_status()


@router.get(
    "/gestures",
    response_model=List[TemporalGestureDefinition],
    summary="List supported dynamic gestures",
    description="Returns catalog of 9 temporal gestures (T001-T009) with motion specs and experimental status.",
)
async def list_temporal_gestures() -> List[TemporalGestureDefinition]:
    return list(TEMPORAL_GESTURE_CATALOG.values())


@router.get(
    "/events",
    response_model=List[TemporalGestureEvent],
    summary="Get recent temporal gesture events",
    description="Returns historical ring buffer of recently triggered dynamic gesture events.",
)
async def get_temporal_events(
    limit: int = Query(default=20, ge=1, le=100, description="Max events to return"),
) -> List[TemporalGestureEvent]:
    engine = get_temporal_engine()
    return engine.get_recent_events(limit=limit)


@router.post(
    "/reset",
    summary="Reset temporal buffers and state machines",
    description="Clears all active observation windows and resets tracking states to IDLE.",
)
async def reset_temporal_engine() -> Dict[str, Any]:
    engine = get_temporal_engine()
    engine.reset()
    return {"success": True, "message": "Temporal gesture engine reset to IDLE."}


# --- Temporal Sequence Dataset Collection Endpoints ---


@router.post(
    "/dataset/start",
    response_model=TemporalCollectionStatus,
    summary="Start temporal sequence recording",
    description="Begins capturing dynamic gesture sequences for the specified gesture ID.",
)
async def start_temporal_collection(
    gesture_id: str = Query(..., description="Target temporal gesture ID (e.g. T001)"),
    session_id: Optional[str] = Query(default=None, description="Optional custom session identifier"),
    target_sequences: int = Query(default=10, ge=1, le=50, description="Target sequence quota"),
) -> TemporalCollectionStatus:
    if gesture_id not in TEMPORAL_GESTURE_CATALOG:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown temporal gesture ID '{gesture_id}'. Valid IDs: {list(TEMPORAL_GESTURE_CATALOG.keys())}",
        )

    tds = get_temporal_dataset_service()
    return tds.start_collection(
        gesture_id=gesture_id,
        session_id=session_id,
        target_sequences=target_sequences,
    )


@router.post(
    "/dataset/commit",
    response_model=Optional[TemporalSequenceSample],
    summary="Commit current sequence to disk",
    description="Validates and persists the sequence accumulated so far as an atomic JSON sample.",
)
async def commit_temporal_sequence() -> Optional[TemporalSequenceSample]:
    tds = get_temporal_dataset_service()
    sample = tds.commit_sequence()
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot commit sequence: Insufficient frames (need >= 8) or duration too short (< 120ms).",
        )
    return sample


@router.post(
    "/dataset/stop",
    response_model=TemporalCollectionStatus,
    summary="Stop temporal collection",
    description="Terminates active sequence recording session.",
)
async def stop_temporal_collection() -> TemporalCollectionStatus:
    tds = get_temporal_dataset_service()
    return tds.stop_collection()


@router.get(
    "/dataset/status",
    response_model=TemporalCollectionStatus,
    summary="Get temporal sequence collection status",
)
async def get_temporal_collection_status() -> TemporalCollectionStatus:
    tds = get_temporal_dataset_service()
    return tds.get_collection_status()


@router.get(
    "/dataset/stats",
    summary="Get temporal dataset statistics",
    description="Aggregates sequence counts, total frames, and average durations per dynamic gesture on disk.",
)
async def get_temporal_dataset_stats() -> Dict[str, Any]:
    tds = get_temporal_dataset_service()
    return tds.get_dataset_stats()
