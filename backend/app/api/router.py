"""
Central API router for GestureFlow AI backend.

Aggregates all route modules under the versioned API prefix.
"""

from fastapi import APIRouter

from app.api.routes import camera, classifier, collection, dataset, gestures, health, mouse, public_datasets, status, temporal, tracking
from app.core.config import settings

# Main API router with versioned prefix
api_router = APIRouter(prefix=settings.api_prefix)

# Include route modules
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(status.router, tags=["Status"])
api_router.include_router(camera.router, tags=["Camera"])
api_router.include_router(tracking.router, tags=["Tracking"])
api_router.include_router(mouse.router, tags=["Mouse Control"])
api_router.include_router(gestures.router, tags=["Gestures"])
api_router.include_router(dataset.router, tags=["Dataset"])
api_router.include_router(collection.router, tags=["Collection"])
api_router.include_router(public_datasets.router, tags=["Public Datasets"])
api_router.include_router(classifier.classifier_router, tags=["Classifier"])
api_router.include_router(classifier.models_router, tags=["Models"])
api_router.include_router(temporal.router, tags=["Temporal Gesture Recognition"])


@api_router.get(
    "/",
    summary="API root",
    description="Basic API information",
    include_in_schema=False,
)
async def api_root() -> dict:
    """API root endpoint with basic information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "prefix": settings.api_prefix,
        "docs": "/docs",
        "health": f"{settings.api_prefix}/health",
        "status": f"{settings.api_prefix}/status",
        "camera": f"{settings.api_prefix}/camera",
        "tracking": f"{settings.api_prefix}/tracking",
        "gestures": f"{settings.api_prefix}/gestures",
        "dataset": f"{settings.api_prefix}/dataset",
        "collection": f"{settings.api_prefix}/collection",
        "public_datasets": f"{settings.api_prefix}/public-datasets",
    }