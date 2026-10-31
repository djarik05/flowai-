"""
Dataset management and export routes for GestureFlow AI backend.

Provides endpoints for querying dataset samples, statistics, integrity validation,
and CSV/JSON file exports.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.schemas.dataset import (
    DatasetSample,
    DatasetStatsResponse,
    DatasetValidationReport,
    SampleListResponse,
)
from app.schemas.public_dataset import (
    DatasetCombineRequest,
    DatasetCombineResponse,
    DatasetSourcesResponse,
)
from app.services.dataset_combiner import DatasetCombinerService
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService

router = APIRouter(prefix="/dataset", tags=["Dataset"])

_dataset_service: Optional[DatasetService] = None
_gesture_service: Optional[GestureService] = None
_combiner_service: Optional[DatasetCombinerService] = None


def get_dataset_service() -> DatasetService:
    """Get dataset service instance."""
    global _dataset_service
    if _dataset_service is None:
        _dataset_service = DatasetService()
    return _dataset_service


def get_gesture_service() -> GestureService:
    """Get gesture service instance."""
    global _gesture_service
    if _gesture_service is None:
        _gesture_service = GestureService()
    return _gesture_service


def get_combiner_service() -> DatasetCombinerService:
    """Get dataset combiner service instance."""
    global _combiner_service
    if _combiner_service is None:
        _combiner_service = DatasetCombinerService()
    return _combiner_service


@router.get(
    "/stats",
    response_model=DatasetStatsResponse,
    summary="Get dataset statistics",
    description="Returns aggregated metrics: total samples, completion %, samples per gesture.",
)
async def get_dataset_stats() -> DatasetStatsResponse:
    """Get aggregated dataset statistics for the dashboard."""
    dataset_svc = get_dataset_service()
    gesture_svc = get_gesture_service()

    registered_gestures = [g.model_dump() for g in gesture_svc.get_all()]
    return dataset_svc.get_stats(registered_gestures=registered_gestures)


@router.get(
    "/samples",
    response_model=SampleListResponse,
    summary="List dataset samples",
    description="Returns paginated list of samples with optional gesture and session filters.",
)
async def list_samples(
    gesture_id: Optional[str] = Query(default=None, description="Filter by gesture ID"),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID"),
    limit: int = Query(default=50, ge=1, le=500, description="Items per page"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> SampleListResponse:
    """Query paginated dataset samples."""
    dataset_svc = get_dataset_service()
    samples, total = dataset_svc.get_samples(
        gesture_id=gesture_id,
        session_id=session_id,
        limit=limit,
        offset=offset,
    )
    return SampleListResponse(
        samples=samples,
        total=total,
        limit=limit,
        offset=offset,
        gesture_id=gesture_id,
    )


@router.post(
    "/samples",
    response_model=DatasetSample,
    status_code=status.HTTP_201_CREATED,
    summary="Create and persist a dataset sample",
    description="Validates and atomically persists a 21-point hand landmark dataset sample.",
)
async def create_sample(sample: DatasetSample) -> DatasetSample:
    """Save a validated dataset sample."""
    dataset_svc = get_dataset_service()
    try:
        saved = dataset_svc.save_sample(sample)
        return saved
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to persist sample: {e}",
        )


@router.get(
    "/samples/{sample_id}",
    response_model=DatasetSample,
    summary="Get single sample details",
    description="Returns full landmark coordinates and metadata for a specific sample.",
)
async def get_sample_details(sample_id: str) -> DatasetSample:
    """Get full sample details with 21 coordinates."""
    dataset_svc = get_dataset_service()
    sample = dataset_svc.get_sample(sample_id)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample with ID '{sample_id}' not found.",
        )
    return sample


@router.delete(
    "/samples/{sample_id}",
    summary="Delete a sample",
    description="Permanently deletes an individual dataset sample.",
)
async def delete_sample(sample_id: str) -> dict:
    """Delete an individual sample."""
    dataset_svc = get_dataset_service()
    success = dataset_svc.delete_sample(sample_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample with ID '{sample_id}' not found.",
        )
    return {
        "success": True,
        "message": f"Sample '{sample_id}' deleted successfully.",
    }


@router.delete(
    "/sessions/{session_id}",
    summary="Delete a collection session",
    description="Deletes all samples captured during a specific session.",
)
async def delete_session(session_id: str) -> dict:
    """Delete all samples from a session."""
    dataset_svc = get_dataset_service()
    count = dataset_svc.delete_session(session_id)
    return {
        "success": True,
        "message": f"Deleted {count} samples from session '{session_id}'.",
        "deleted_count": count,
    }


@router.get(
    "/validate",
    response_model=DatasetValidationReport,
    summary="Validate dataset integrity",
    description="Performs an audit check for missing landmarks, corrupted files, and duplicate IDs.",
)
async def validate_dataset() -> DatasetValidationReport:
    """Perform dataset validation audit."""
    dataset_svc = get_dataset_service()
    gesture_svc = get_gesture_service()

    registered_ids = {g.id for g in gesture_svc.get_all()}
    report = dataset_svc.validate_dataset(registered_ids=registered_ids)
    return report


@router.get(
    "/export/csv",
    summary="Export dataset to CSV",
    description="Downloads flattened landmark dataset as a CSV file.",
)
async def export_csv(
    gesture_id: Optional[str] = Query(default=None, description="Optional gesture ID filter"),
):
    """Export dataset to CSV."""
    dataset_svc = get_dataset_service()
    csv_path = dataset_svc.export_csv(gesture_id=gesture_id)
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=csv_path.name,
    )


@router.get(
    "/export/json",
    summary="Export dataset to JSON",
    description="Downloads complete structured dataset archive as a JSON file.",
)
async def export_json(
    gesture_id: Optional[str] = Query(default=None, description="Optional gesture ID filter"),
):
    """Export dataset to JSON."""
    dataset_svc = get_dataset_service()
    json_path = dataset_svc.export_json(gesture_id=gesture_id)
    return FileResponse(
        path=str(json_path),
        media_type="application/json",
        filename=json_path.name,
    )


@router.get(
    "/sources",
    response_model=DatasetSourcesResponse,
    summary="Get overview of all dataset sources",
    description="Summarizes custom and public HaGRID sample counts, coordinate formats, and gesture breakdown.",
)
async def get_dataset_sources() -> DatasetSourcesResponse:
    """Get sample counts and coordinate formats for all dataset sources."""
    combiner = get_combiner_service()
    return combiner.get_sources_overview()


@router.post(
    "/combine",
    response_model=DatasetCombineResponse,
    summary="Combine datasets into ML-ready package",
    description="Combines custom and HaGRID samples with coordinate validation and leakage-free splits.",
)
async def combine_datasets(request: DatasetCombineRequest) -> DatasetCombineResponse:
    """Create a unified dataset version across sources."""
    combiner = get_combiner_service()
    try:
        return combiner.combine_datasets(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/combined",
    summary="List combined dataset versions",
    description="Returns metadata of all combined datasets available for export or training.",
)
async def list_combined_datasets() -> List[Dict[str, Any]]:
    """List all combined dataset packages."""
    combiner = get_combiner_service()
    return combiner.list_combined_datasets()


@router.get(
    "/combined/{combined_id}/export/{format}",
    summary="Download combined dataset export",
    description="Downloads combined CSV or JSON dataset package.",
)
async def download_combined_export(combined_id: str, format: str):
    """Download combined dataset file."""
    combiner = get_combiner_service()
    target_dir = combiner._combined_dir / combined_id
    if not target_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Combined dataset '{combined_id}' not found.",
        )

    if format.lower() == "csv":
        fpath = target_dir / "combined_dataset.csv"
        media = "text/csv"
    elif format.lower() == "json":
        fpath = target_dir / "combined_dataset.json"
        media = "application/json"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format must be 'csv' or 'json'.",
        )

    if not fpath.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export file {fpath.name} not found in {combined_id}.",
        )

    return FileResponse(
        path=str(fpath),
        media_type=media,
        filename=f"combined_{combined_id}.{format.lower()}",
    )
