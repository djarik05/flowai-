"""
Schemas package for GestureFlow AI backend.

Exports all Pydantic models for request/response validation.
"""

from app.schemas.camera import (
    CameraConfigRequest,
    CameraConfigResponse,
    CameraInfo,
    CameraState,
    CameraStatusResponse,
)
from app.schemas.common import (
    APIInfo,
    BaseSchema,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    SuccessResponse,
)
from app.schemas.status import BackendState, ComponentState, ModelState, StatusResponse
from app.schemas.tracking import (
    DetectedHand,
    Landmark,
    TrackingConfigRequest,
    TrackingConfigResponse,
    TrackingResult,
    TrackingState,
    TrackingStatusResponse,
)

__all__ = [
    # Common
    "APIInfo",
    "BaseSchema",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "SuccessResponse",
    # Status
    "BackendState",
    "ComponentState",
    "ModelState",
    "StatusResponse",
    # Camera
    "CameraConfigRequest",
    "CameraConfigResponse",
    "CameraInfo",
    "CameraState",
    "CameraStatusResponse",
    # Tracking
    "DetectedHand",
    "Landmark",
    "TrackingConfigRequest",
    "TrackingConfigResponse",
    "TrackingResult",
    "TrackingState",
    "TrackingStatusResponse",
]