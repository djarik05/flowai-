"""
Classifier and Model Registry routes for GestureFlow AI backend.

Endpoints:
- GET  /api/v1/classifier/status
- GET  /api/v1/classifier/dataset-readiness
- POST /api/v1/classifier/train
- GET  /api/v1/classifier/train/{job_id}
- POST /api/v1/classifier/predict
- POST /api/v1/classifier/seed-samples

- GET    /api/v1/models
- GET    /api/v1/models/active
- GET    /api/v1/models/compare
- GET    /api/v1/models/{model_id}
- POST   /api/v1/models/{model_id}/activate
- POST   /api/v1/models/{model_id}/deactivate
- DELETE /api/v1/models/{model_id}
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.classifier import (
    ClassifierStatusResponse,
    DatasetReadinessReport,
    ModelMetadata,
    PredictionRequest,
    PredictionResponse,
    TrainingConfigRequest,
    TrainingJobStatus,
)
from app.services.classifier_service import ClassifierService, get_classifier_service
from app.services.dataset_readiness import DatasetReadinessAnalyzer
from app.services.dataset_seeder import DatasetSeeder
from app.services.model_registry import ModelRegistryService
from app.services.training_engine import TrainingEngine

classifier_router = APIRouter(prefix="/classifier", tags=["Classifier"])
models_router = APIRouter(prefix="/models", tags=["Models"])

_training_engine: Optional[TrainingEngine] = None
_readiness_analyzer: Optional[DatasetReadinessAnalyzer] = None
_model_registry: Optional[ModelRegistryService] = None
_dataset_seeder: Optional[DatasetSeeder] = None


def get_training_engine() -> TrainingEngine:
    global _training_engine
    if _training_engine is None:
        _training_engine = TrainingEngine(registry_service=get_model_registry())
    return _training_engine


def get_readiness_analyzer() -> DatasetReadinessAnalyzer:
    global _readiness_analyzer
    if _readiness_analyzer is None:
        _readiness_analyzer = DatasetReadinessAnalyzer()
    return _readiness_analyzer


def get_model_registry() -> ModelRegistryService:
    global _model_registry
    if _model_registry is None:
        _model_registry = ModelRegistryService()
    return _model_registry


def get_dataset_seeder() -> DatasetSeeder:
    global _dataset_seeder
    if _dataset_seeder is None:
        _dataset_seeder = DatasetSeeder()
    return _dataset_seeder


# ===========================================================================
# Classifier & Training Endpoints
# ===========================================================================


@classifier_router.get(
    "/status",
    response_model=ClassifierStatusResponse,
    summary="Get classifier engine status",
    description="Returns whether an active model is loaded, active model metadata, and inference latency stats.",
)
async def get_classifier_status() -> ClassifierStatusResponse:
    cls_svc = get_classifier_service()
    return cls_svc.get_status()


@classifier_router.get(
    "/dataset-readiness",
    response_model=DatasetReadinessReport,
    summary="Audit dataset readiness for training",
    description="Audits all registered gestures on disk, checks sample counts, coordinate formats, and class balance.",
)
async def get_dataset_readiness(
    min_samples: int = Query(default=5, ge=1, le=1000, description="Minimum samples per class required"),
) -> DatasetReadinessReport:
    analyzer = get_readiness_analyzer()
    return analyzer.audit(min_samples=min_samples)


@classifier_router.post(
    "/train",
    response_model=TrainingJobStatus,
    summary="Start model training job",
    description="Initiates background training of a static MLP gesture classifier.",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_training(config: TrainingConfigRequest) -> TrainingJobStatus:
    analyzer = get_readiness_analyzer()
    readiness = analyzer.audit()

    if not readiness.is_training_ready:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start training: {readiness.summary}. {'; '.join(readiness.warnings)}",
        )

    engine = get_training_engine()
    job = engine.start_training_job(config, background=True)
    return job


@classifier_router.get(
    "/train/{job_id}",
    response_model=TrainingJobStatus,
    summary="Get training job progress",
    description="Returns current epoch, training/validation loss curves, and final model ID.",
)
async def get_training_job(job_id: str) -> TrainingJobStatus:
    engine = get_training_engine()
    job = engine.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job '{job_id}' not found.",
        )
    return job


@classifier_router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Real-time landmark classification",
    description="Predicts hand gesture from 21 MediaPipe landmark coordinates using active model.",
)
async def predict_gesture(request: PredictionRequest) -> PredictionResponse:
    cls_svc = get_classifier_service()
    return cls_svc.predict_landmarks(
        landmarks=request.landmarks,
        handedness=request.handedness or "Right",
        custom_threshold=request.confidence_threshold,
    )


@classifier_router.post(
    "/seed-samples",
    summary="Seed standard gesture dataset",
    description="Populates verified 3D samples for standard registered gestures to facilitate immediate multi-class training.",
)
async def seed_samples(
    samples_per_gesture: int = Query(default=15, ge=5, le=50),
) -> Dict[str, Any]:
    seeder = get_dataset_seeder()
    seeded = seeder.seed_standard_gestures(samples_per_gesture=samples_per_gesture)
    return {
        "success": True,
        "message": f"Successfully seeded samples across {len(seeded)} gestures.",
        "seeded": seeded,
    }


# ===========================================================================
# Model Registry Endpoints
# ===========================================================================


@models_router.get(
    "",
    response_model=List[ModelMetadata],
    summary="List registered models",
    description="Returns all versioned model checkpoints and their test metrics.",
)
async def list_models() -> List[ModelMetadata]:
    registry = get_model_registry()
    return registry.list_models()


@models_router.get(
    "/active",
    response_model=Optional[ModelMetadata],
    summary="Get active model details",
    description="Returns metadata of the model currently loaded for real-time inference.",
)
async def get_active_model() -> Optional[ModelMetadata]:
    registry = get_model_registry()
    return registry.get_active_model()


@models_router.get(
    "/compare",
    summary="Compare two models",
    description="Returns diff of evaluation metrics between two registered models.",
)
async def compare_models(
    model_a: str = Query(..., description="First model ID"),
    model_b: str = Query(..., description="Second model ID"),
) -> Dict[str, Any]:
    registry = get_model_registry()
    try:
        return registry.compare_models(model_a, model_b)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@models_router.get(
    "/{model_id}",
    response_model=ModelMetadata,
    summary="Get model metadata",
    description="Retrieve details, architecture, and evaluation metrics for a specific model.",
)
async def get_model_details(model_id: str) -> ModelMetadata:
    registry = get_model_registry()
    model = registry.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found in registry.",
        )
    return model


@models_router.post(
    "/{model_id}/activate",
    summary="Activate model for real-time inference",
    description="Sets the specified model as active and hot-reloads it in the live inference pipeline.",
)
async def activate_model(model_id: str) -> Dict[str, Any]:
    registry = get_model_registry()
    success = registry.activate_model(model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found or could not be activated.",
        )

    # Hot-reload in classifier service
    cls_svc = get_classifier_service()
    reloaded = cls_svc.load_active_model(force=True)

    return {
        "success": True,
        "message": f"Model '{model_id}' activated successfully.",
        "model_id": model_id,
        "in_memory_loaded": reloaded,
    }


@models_router.post(
    "/{model_id}/deactivate",
    summary="Deactivate model",
    description="Deactivates currently active model.",
)
async def deactivate_model(model_id: str) -> Dict[str, Any]:
    registry = get_model_registry()
    success = registry.deactivate_model(model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model_id}' is not the currently active model.",
        )

    cls_svc = get_classifier_service()
    cls_svc.load_active_model(force=True)

    return {
        "success": True,
        "message": f"Model '{model_id}' deactivated.",
    }


@models_router.delete(
    "/{model_id}",
    summary="Delete model",
    description="Permanently deletes model checkpoint files and removes from registry.",
)
async def delete_model(model_id: str) -> Dict[str, Any]:
    registry = get_model_registry()
    success = registry.delete_model(model_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' not found.",
        )

    cls_svc = get_classifier_service()
    if cls_svc._active_metadata_id == model_id:
        cls_svc.load_active_model(force=True)

    return {
        "success": True,
        "message": f"Model '{model_id}' deleted successfully.",
    }
