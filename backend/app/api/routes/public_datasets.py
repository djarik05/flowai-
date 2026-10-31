"""
Public dataset API routes for GestureFlow AI backend.

Provides endpoints for HaGRID dataset inspection, selective downloading,
class mapping configuration, annotation importing, and validation reporting.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.public_dataset import (
    HagridClassInfo,
    HagridClassMapping,
    HagridClassMappingsResponse,
    HagridDatasetInfo,
    HagridDownloadRequest,
    HagridImportRequest,
    PublicJobStatusResponse,
)
from app.services.gesture_service import GestureService
from app.services.hagrid_constants import (
    DATASET_ATTRIBUTION_METADATA,
    HAGRID_CLASS_DESCRIPTIONS,
    HAGRID_CLASS_SIZES,
    HAGRID_GESTURE_URLS,
    TWO_HANDED_GESTURES,
)
from app.services.hagrid_downloader import HagridDownloadManager
from app.services.hagrid_importer import HagridImporterService

router = APIRouter(prefix="/public-datasets", tags=["Public Datasets"])

_download_manager: Optional[HagridDownloadManager] = None
_importer_service: Optional[HagridImporterService] = None
_gesture_service: Optional[GestureService] = None


def get_download_manager() -> HagridDownloadManager:
    """Get or create singleton download manager."""
    global _download_manager
    if _download_manager is None:
        _download_manager = HagridDownloadManager()
    return _download_manager


def get_importer_service() -> HagridImporterService:
    """Get or create singleton importer service."""
    global _importer_service, _download_manager, _gesture_service
    if _importer_service is None:
        dl_mgr = get_download_manager()
        gesture_svc = get_gesture_service()
        _importer_service = HagridImporterService(
            download_manager=dl_mgr,
            gesture_service=gesture_svc,
        )
    return _importer_service


def get_gesture_service() -> GestureService:
    """Get or create singleton gesture service."""
    global _gesture_service
    if _gesture_service is None:
        _gesture_service = GestureService()
    return _gesture_service


@router.get(
    "",
    summary="List supported public datasets",
    description="Returns high-level metadata of supported external datasets.",
)
async def list_public_datasets() -> List[Dict[str, Any]]:
    """List all available public datasets."""
    importer = get_importer_service()
    counts = importer.get_imported_sample_counts()
    total_imported = sum(counts.values())

    return [
        {
            "id": "hagrid",
            "name": "HaGRIDv2",
            "full_name": "HAnd Gesture Recognition Image Dataset v2",
            "classes_count": 34,
            "total_samples": 1086158,
            "total_size_tb": 1.5,
            "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "attribution": DATASET_ATTRIBUTION_METADATA,
            "imported_samples": total_imported,
            "is_supported": True,
        }
    ]


@router.get(
    "/hagrid",
    response_model=HagridDatasetInfo,
    summary="Get HaGRID dataset metadata and download status",
    description="Returns official HaGRID metadata, class catalog, sizes, license notice, and local storage state.",
)
async def get_hagrid_info() -> HagridDatasetInfo:
    """Get HaGRIDv2 overview, class list, and local status."""
    importer = get_importer_service()
    dl_mgr = get_download_manager()

    manifest = dl_mgr._load_manifest()
    downloaded_classes = list(manifest.get("downloads", {}).keys())
    annotations_downloaded = "annotations" in manifest.get("downloads", {})

    mappings = importer.load_mappings()
    imported_counts = importer.get_imported_sample_counts()

    # Build class info list
    classes: List[HagridClassInfo] = []
    for c_name, c_url in HAGRID_GESTURE_URLS.items():
        size = HAGRID_CLASS_SIZES.get(c_name, 42.0)
        desc = HAGRID_CLASS_DESCRIPTIONS.get(c_name, "")
        is_2h = c_name in TWO_HANDED_GESTURES
        mapping = mappings.get(c_name, {})

        classes.append(
            HagridClassInfo(
                name=c_name,
                size_gb=size,
                sample_count_approx=2164 if c_name == "no_gesture" else 32000,
                description=desc,
                is_two_handed=is_2h,
                download_url=c_url,
                suggested_gesture_id=mapping.get("target_id"),
                suggested_gesture_name=mapping.get("target_name"),
            )
        )

    return HagridDatasetInfo(
        classes=classes,
        downloaded_classes=downloaded_classes,
        annotations_downloaded=annotations_downloaded,
        imported_sample_counts=imported_counts,
    )


@router.get(
    "/hagrid/classes",
    response_model=List[HagridClassInfo],
    summary="Get HaGRID class catalog",
    description="Lists all 34 HaGRID gesture classes with approximate sizes and suggested mappings.",
)
async def get_hagrid_classes() -> List[HagridClassInfo]:
    """Get all 34 HaGRID classes."""
    info = await get_hagrid_info()
    return info.classes


@router.get(
    "/hagrid/mappings",
    response_model=HagridClassMappingsResponse,
    summary="Get HaGRID class mappings",
    description="Returns current mappings between HaGRID classes and GestureFlow gestures.",
)
async def get_hagrid_mappings() -> HagridClassMappingsResponse:
    """Get class mappings configuration."""
    importer = get_importer_service()
    gesture_svc = get_gesture_service()

    mappings_dict = importer.load_mappings()
    typed_mappings: Dict[str, HagridClassMapping] = {}

    for k, v in mappings_dict.items():
        typed_mappings[k] = HagridClassMapping(
            hagrid_class=k,
            target_gesture_id=v.get("target_id"),
            target_gesture_name=v.get("target_name"),
            action=v.get("action", "map"),
            confidence_threshold=v.get("confidence_threshold", 0.8),
        )

    available_gestures = [
        {"id": g.id, "name": g.name, "type": g.type}
        for g in gesture_svc.get_all()
    ]

    return HagridClassMappingsResponse(
        mappings=typed_mappings,
        available_gestures=available_gestures,
    )


@router.put(
    "/hagrid/mappings",
    response_model=Dict[str, Any],
    summary="Update HaGRID class mappings",
    description="Saves custom mappings between HaGRID classes and GestureFlow gestures.",
)
async def update_hagrid_mappings(mappings: Dict[str, HagridClassMapping]) -> Dict[str, Any]:
    """Save updated class mappings."""
    importer = get_importer_service()
    raw_dict = {k: v.model_dump() for k, v in mappings.items()}
    importer.set_all_mappings(raw_dict)
    return {"status": "success", "message": f"Updated {len(mappings)} class mappings."}


@router.post(
    "/hagrid/download",
    response_model=PublicJobStatusResponse,
    summary="Start selective HaGRID download",
    description="Initiates background chunked streaming download of selected annotations and gesture archives.",
)
async def start_hagrid_download(request: HagridDownloadRequest) -> PublicJobStatusResponse:
    """Start selective download job."""
    dl_mgr = get_download_manager()

    job_id = dl_mgr.start_download_job(
        download_annotations=request.download_annotations,
        target_classes=request.target_classes,
        force_redownload=request.force_redownload,
    )

    job_status = dl_mgr.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize download job.",
        )
    return job_status


@router.get(
    "/download/{job_id}",
    response_model=PublicJobStatusResponse,
    summary="Get download job status",
    description="Polls progress, download speed, and completion status of a download job.",
)
async def get_download_status(job_id: str) -> PublicJobStatusResponse:
    """Poll download status."""
    dl_mgr = get_download_manager()
    job_status = dl_mgr.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download job '{job_id}' not found.",
        )
    return job_status


@router.post(
    "/download/{job_id}/cancel",
    summary="Cancel download job",
    description="Cancels an active download job and cleans up partial downloads.",
)
async def cancel_download_job(job_id: str) -> Dict[str, Any]:
    """Cancel active download."""
    dl_mgr = get_download_manager()
    success = dl_mgr.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active download job '{job_id}' not found or already completed.",
        )
    return {"status": "cancelled", "job_id": job_id}


@router.post(
    "/hagrid/import",
    response_model=PublicJobStatusResponse,
    summary="Start HaGRID annotation import",
    description="Initiates background parsing and conversion of annotations into GestureFlow DatasetSamples.",
)
async def start_hagrid_import(request: HagridImportRequest) -> PublicJobStatusResponse:
    """Start annotation import job."""
    importer = get_importer_service()

    job_id = importer.start_import_job(
        source_type=request.source_type,
        local_annotation_path=request.local_annotation_path,
        splits=request.splits,
        selected_classes=request.selected_classes,
        max_samples_per_class=request.max_samples_per_class,
    )

    job_status = importer.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize import job.",
        )
    return job_status


@router.get(
    "/import/{job_id}",
    response_model=PublicJobStatusResponse,
    summary="Get import job status",
    description="Polls progress, parsed sample counts, and completion status of an import job.",
)
async def get_import_status(job_id: str) -> PublicJobStatusResponse:
    """Poll import status."""
    importer = get_importer_service()
    job_status = importer.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_id}' not found.",
        )
    return job_status


@router.post(
    "/import/{job_id}/cancel",
    summary="Cancel import job",
    description="Cancels an active import job.",
)
async def cancel_import_job(job_id: str) -> Dict[str, Any]:
    """Cancel active import."""
    importer = get_importer_service()
    success = importer.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active import job '{job_id}' not found or already completed.",
        )
    return {"status": "cancelled", "job_id": job_id}


@router.get(
    "/validation/{job_id}",
    summary="Get import validation report",
    description="Returns detailed audit logs and issues detected during an import session.",
)
async def get_import_validation(job_id: str) -> Dict[str, Any]:
    """Get audit report for import job."""
    importer = get_importer_service()
    manifest_file = importer._manifests_dir / f"import_manifest_{job_id}.json"
    if not manifest_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation manifest for job '{job_id}' not found.",
        )

    with open(manifest_file, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/samples",
    summary="Browse imported HaGRID samples",
    description="Query imported samples with pagination and gesture/split filtering.",
)
async def list_imported_samples(
    gesture_id: Optional[str] = Query(default=None),
    split: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List imported samples."""
    importer = get_importer_service()
    samples, total = importer.get_imported_samples(
        gesture_id=gesture_id,
        split=split,
        limit=limit,
        offset=offset,
    )
    return {
        "samples": [s.model_dump() for s in samples],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
