"""
Temporal gesture recognition and sequence dataset schemas for GestureFlow AI Phase 5.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StateMachineState(str, Enum):
    """Gesture state machine operational states."""
    IDLE = "IDLE"
    CANDIDATE = "CANDIDATE"
    TRACKING = "TRACKING"
    RECOGNIZED = "RECOGNIZED"
    COOLDOWN = "COOLDOWN"


class TemporalGestureDefinition(BaseModel):
    """Specification of a dynamic gesture."""
    id: str = Field(..., description="Unique gesture identifier (e.g. T001)")
    name: str = Field(..., description="Human-readable gesture name")
    description: str = Field(..., description="Detailed gesture description")
    expected_motion: str = Field(..., description="Expected spatial/temporal trajectory")
    is_experimental: bool = Field(default=False, description="Flag for gestures with single-camera depth sensitivity")
    min_duration_ms: float = Field(default=150.0, description="Minimum duration threshold in milliseconds")
    max_duration_ms: float = Field(default=1000.0, description="Maximum duration threshold in milliseconds")
    cooldown_ms: float = Field(default=500.0, description="Cooldown duration following recognition")

    model_config = {"protected_namespaces": ()}


class TemporalGestureEvent(BaseModel):
    """Unified temporal gesture event emitted when motion criteria are met."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(default="temporal_gesture", description="Event category discriminator")
    gesture_id: str = Field(..., description="Recognized temporal gesture ID")
    gesture_name: str = Field(..., description="Recognized gesture name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    status: str = Field(default="recognized", description="Event status: recognized, candidate, or completed")
    timestamp: float = Field(..., description="Monotonic timestamp in seconds")
    handedness: str = Field(default="Right", description="Handedness label (Left/Right)")
    duration_ms: float = Field(..., description="Duration of gesture motion in milliseconds")
    velocity: float = Field(default=0.0, description="Velocity magnitude in normalized units/second")
    direction: str = Field(default="none", description="Primary movement direction")
    displacement: Dict[str, float] = Field(default_factory=dict, description="Net spatial displacement (dx, dy, dz)")

    model_config = {"protected_namespaces": ()}


class MovementTelemetry(BaseModel):
    """Real-time movement statistics for a tracked hand."""
    hand_id: int = Field(default=0, description="Tracked hand index")
    handedness: str = Field(default="Right", description="Handedness label")
    state: StateMachineState = Field(default=StateMachineState.IDLE, description="Current state machine phase")
    current_position: Dict[str, float] = Field(default_factory=dict, description="Current centroid / wrist (x, y, z)")
    velocity: Dict[str, float] = Field(default_factory=dict, description="vx, vy, vz, speed")
    direction: str = Field(default="none", description="Primary instantaneous direction")
    linearity: float = Field(default=1.0, description="Trajectory linearity score [0, 1]")
    path_length: float = Field(default=0.0, description="Cumulative distance traveled")
    buffer_size: int = Field(default=0, description="Observations currently stored in buffer")
    duration_ms: float = Field(default=0.0, description="Active motion window duration in ms")

    model_config = {"protected_namespaces": ()}


class TemporalEngineStatusResponse(BaseModel):
    """Detailed operational status of the temporal gesture recognition engine."""
    is_active: bool = Field(default=True, description="Whether temporal engine is active")
    hands_tracked: int = Field(default=0, description="Number of currently active hand buffers")
    active_gestures_count: int = Field(default=9, description="Number of registered temporal gestures")
    total_events_recognized: int = Field(default=0, description="Cumulative temporal gesture events triggered")
    recent_events: List[TemporalGestureEvent] = Field(default_factory=list, description="Recent event ring buffer")
    movement_telemetry: Dict[str, MovementTelemetry] = Field(default_factory=dict, description="Telemetry by handedness")
    avg_processing_latency_ms: float = Field(default=0.0, description="Average temporal feature processing latency")

    model_config = {"protected_namespaces": ()}


class TemporalSequenceSample(BaseModel):
    """Persisted temporal gesture sequence recording."""
    sample_id: str = Field(..., description="Unique sample identifier")
    gesture_id: str = Field(..., description="Target temporal gesture ID")
    gesture_name: str = Field(..., description="Target gesture name")
    handedness: str = Field(default="Right", description="Handedness used")
    session_id: str = Field(..., description="Recording session identifier")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    duration_ms: float = Field(..., description="Sequence duration in milliseconds")
    frame_count: int = Field(..., description="Number of frames recorded in sequence")
    timestamps: List[float] = Field(..., description="Monotonic timestamp sequence in seconds")
    landmarks_sequence: List[List[Dict[str, Any]]] = Field(..., description="Frames of 21 landmark points")
    camera_metadata: Dict[str, Any] = Field(default_factory=dict, description="Resolution, FPS, device index")
    dataset_version: str = Field(default="1.0.0", description="Dataset schema version")

    model_config = {"protected_namespaces": ()}


class TemporalCollectionStatus(BaseModel):
    """Status of dynamic gesture sequence recorder."""
    is_collecting: bool = Field(default=False, description="Whether a sequence collection session is ongoing")
    gesture_id: Optional[str] = Field(default=None, description="Active target gesture ID")
    session_id: Optional[str] = Field(default=None, description="Current recording session ID")
    target_sequences: int = Field(default=10, description="Target sequence count")
    collected_sequences: int = Field(default=0, description="Successfully persisted sequences")
    current_sequence_frames: int = Field(default=0, description="Frames captured in currently recording sequence")

    model_config = {"protected_namespaces": ()}
