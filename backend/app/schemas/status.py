"""
Status schemas for GestureFlow AI backend.

Defines typed response models for the application status endpoint.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ComponentState(str, Enum):
    """Possible states for backend components."""

    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class BackendState(str, Enum):
    """Overall backend state."""

    STARTING = "starting"
    READY = "ready"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class ModelState(str, Enum):
    """Model-specific states."""

    NOT_LOADED = "not_loaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"


class StatusResponse(BaseModel):
    """
    Application status response (Phase 1 version).

    Uses explicit state enums rather than ambiguous booleans.
    Reflects actual implementation status - does not claim functionality
    that has not been implemented in Phase 1.
    """

    application: str = Field(default="GestureFlow AI", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(..., description="Runtime environment")
    backend_state: BackendState = Field(..., description="Overall backend state")
    current_phase: int = Field(default=1, ge=1, description="Current implementation phase")
    camera_state: ComponentState = Field(default=ComponentState.NOT_INITIALIZED, description="Camera manager state")
    tracking_state: ComponentState = Field(default=ComponentState.NOT_INITIALIZED, description="Hand tracking state")
    model_state: ModelState = Field(default=ModelState.NOT_LOADED, description="Gesture model state")
    controller_state: ComponentState = Field(default=ComponentState.DISABLED, description="OS controller state")

    model_config = {
        "protected_namespaces": (),
        "json_schema_extra": {
            "example": {
                "application": "GestureFlow AI",
                "version": "1.0.0",
                "environment": "development",
                "backend_state": "ready",
                "current_phase": 1,
                "camera_state": "not_initialized",
                "tracking_state": "not_initialized",
                "model_state": "not_loaded",
                "controller_state": "disabled",
            }
        }
    }