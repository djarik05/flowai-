"""
Tracking schemas for GestureFlow AI backend.

Defines typed models for hand tracking API.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class TrackingState(str, Enum):
    """Tracking state enumeration."""

    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    STOPPED = "stopped"


class Landmark(BaseModel):
    """Normalized hand landmark with pixel coordinates."""

    index: int = Field(..., ge=0, le=20, description="Landmark index (0-20)")
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized X coordinate [0, 1]")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized Y coordinate [0, 1]")
    z: float = Field(..., description="Normalized depth coordinate")
    pixel_x: int = Field(..., ge=0, description="Pixel X coordinate")
    pixel_y: int = Field(..., ge=0, description="Pixel Y coordinate")


class DetectedHand(BaseModel):
    """Detected hand with landmarks and metadata."""

    hand_id: int = Field(..., ge=0, description="Hand identifier")
    landmarks: List[Landmark] = Field(..., description="List of 21 hand landmarks")
    handedness: str = Field(default="Unknown", description="Handedness label (Left/Right/Unknown)")
    handedness_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Handedness classification confidence")
    bounding_box: Optional[Dict[str, int]] = Field(
        default=None,
        description="Bounding box: x, y, width, height in pixels"
    )
    timestamp: datetime = Field(default_factory=datetime.now, description="Detection timestamp")
    gesture_id: Optional[str] = Field(default=None, description="Classified gesture ID")
    gesture_name: Optional[str] = Field(default=None, description="Classified gesture name")
    gesture_confidence: Optional[float] = Field(default=None, description="Gesture classification confidence")
    temporal_gesture_id: Optional[str] = Field(default=None, description="Recognized temporal gesture ID")
    temporal_gesture_name: Optional[str] = Field(default=None, description="Recognized temporal gesture name")
    temporal_gesture_confidence: Optional[float] = Field(default=None, description="Temporal gesture confidence")
    temporal_state: Optional[str] = Field(default=None, description="Temporal state machine state (IDLE/TRACKING/etc.)")
    movement_speed: Optional[float] = Field(default=None, description="Instantaneous hand movement speed")
    movement_direction: Optional[str] = Field(default=None, description="Current movement direction")


class TrackingResult(BaseModel):
    """Complete tracking result for a frame."""

    status: TrackingState = Field(..., description="Tracking status")
    frame_width: int = Field(..., ge=0, description="Frame width in pixels")
    frame_height: int = Field(..., ge=0, description="Frame height in pixels")
    hands_detected: int = Field(default=0, ge=0, description="Number of hands detected")
    hands: List[DetectedHand] = Field(default_factory=list, description="Detected hands")
    temporal_events: List[Any] = Field(default_factory=list, description="Temporal gesture events triggered in frame")
    frame_timestamp: datetime = Field(default_factory=datetime.now, description="Frame timestamp")
    processing_time_ms: float = Field(default=0.0, ge=0.0, description="Frame processing time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if status is error")

    model_config = {
        "protected_namespaces": (),
    }


class TrackingStatusResponse(BaseModel):
    """Tracking service status response."""

    state: TrackingState = Field(..., description="Current tracking state")
    camera_active: bool = Field(default=False, description="Whether camera is active")
    detector_initialized: bool = Field(default=False, description="Whether MediaPipe detector is initialized")
    last_tracking_time: Optional[datetime] = Field(default=None, description="Last successful tracking timestamp")
    frames_processed: int = Field(default=0, description="Total frames processed")
    avg_processing_time_ms: float = Field(default=0.0, description="Average processing time in milliseconds")
    actual_inference_fps: float = Field(default=0.0, description="Actual MediaPipe inference framerate")
    camera_fps: float = Field(default=0.0, description="Hardware camera capture framerate")
    end_to_end_latency_ms: float = Field(default=0.0, description="Total frame capture-to-result latency in ms")
    frames_dropped: int = Field(default=0, description="Dropped frames due to inference worker queue limit")
    running_mode: str = Field(default="VIDEO", description="Active inference mode (VIDEO or IMAGE)")
    last_error: Optional[str] = Field(default=None, description="Last error message, if any")

    model_config = {
        "protected_namespaces": (),
    }


class TrackingConfigRequest(BaseModel):
    """Tracking configuration request."""

    max_hands: Optional[int] = Field(default=None, ge=1, le=4, description="Maximum hands to track")
    detection_confidence: Optional[float] = Field(default=None, ge=0.1, le=1.0, description="Detection confidence threshold")
    tracking_confidence: Optional[float] = Field(default=None, ge=0.1, le=1.0, description="Tracking confidence threshold")
    model_complexity: Optional[int] = Field(default=None, ge=0, le=2, description="Model complexity (0=lite, 1=full, 2=heavy)")

    model_config = {
        "protected_namespaces": (),
    }


class TrackingConfigResponse(BaseModel):
    """Tracking configuration response."""

    success: bool = Field(..., description="Whether configuration was applied")
    message: str = Field(..., description="Status message")
    applied_config: Optional[TrackingConfigRequest] = Field(default=None, description="Applied configuration")

    model_config = {
        "protected_namespaces": (),
    }