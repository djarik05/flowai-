"""
Mouse Controller schemas for GestureFlow AI backend Phase 6A, 6B.1 & 6B.2.
"""

from typing import Dict, Optional, Tuple
from pydantic import BaseModel, Field


class MouseSettings(BaseModel):
    """Mouse control configuration settings."""

    sensitivity: float = Field(default=1.0, ge=0.1, le=5.0, description="Cursor movement sensitivity multiplier")
    smoothing_alpha: float = Field(default=0.35, ge=0.01, le=0.99, description="Exponential moving average alpha (lower = smoother)")
    active_margin_x: float = Field(default=0.15, ge=0.0, le=0.40, description="Horizontal tracking margin ratio")
    active_margin_y: float = Field(default=0.15, ge=0.0, le=0.40, description="Vertical tracking margin ratio")
    tracking_timeout_ms: float = Field(default=150.0, ge=50.0, le=1000.0, description="Tracking loss timeout in ms")
    dead_zone: float = Field(default=0.05, ge=0.0, le=0.3, description="Dead zone radius around center [0.0, 1.0]")

    # Phase 6B.1: Gesture-Based Left Click settings (Thumb + Index Pinch, L4 & L8)
    left_click_enabled: bool = Field(default=True, description="Enable gesture-based left mouse click")
    pinch_activation_threshold: float = Field(default=0.05, ge=0.01, le=0.20, description="Pinch distance threshold to trigger left click")
    pinch_release_threshold: float = Field(default=0.08, ge=0.02, le=0.30, description="Pinch distance threshold required to reset pinch state")
    click_cooldown_ms: float = Field(default=400.0, ge=100.0, le=2000.0, description="Minimum cooldown between clicks in ms")

    # Phase 6B.2: Gesture-Based Right Click settings (Thumb + Middle Pinch, L4 & L12)
    right_click_enabled: bool = Field(default=True, description="Enable gesture-based right mouse click")
    right_pinch_activation_threshold: float = Field(default=0.05, ge=0.01, le=0.20, description="Middle-finger pinch distance threshold to trigger right click")
    right_pinch_release_threshold: float = Field(default=0.08, ge=0.02, le=0.30, description="Middle-finger pinch release threshold for hysteresis")
    right_click_cooldown_ms: float = Field(default=500.0, ge=100.0, le=2000.0, description="Minimum cooldown between right clicks in ms")


class MouseSettingsUpdateRequest(BaseModel):
    """Partial update request for mouse settings."""

    sensitivity: Optional[float] = Field(None, ge=0.1, le=5.0)
    smoothing_alpha: Optional[float] = Field(None, ge=0.01, le=0.99)
    active_margin_x: Optional[float] = Field(None, ge=0.0, le=0.40)
    active_margin_y: Optional[float] = Field(None, ge=0.0, le=0.40)
    tracking_timeout_ms: Optional[float] = Field(None, ge=50.0, le=1000.0)
    dead_zone: Optional[float] = Field(None, ge=0.0, le=0.3)

    # Phase 6B.1 Left Click updates
    left_click_enabled: Optional[bool] = None
    pinch_activation_threshold: Optional[float] = Field(None, ge=0.01, le=0.20)
    pinch_release_threshold: Optional[float] = Field(None, ge=0.02, le=0.30)
    click_cooldown_ms: Optional[float] = Field(None, ge=100.0, le=2000.0)

    # Phase 6B.2 Right Click updates
    right_click_enabled: Optional[bool] = None
    right_pinch_activation_threshold: Optional[float] = Field(None, ge=0.01, le=0.20)
    right_pinch_release_threshold: Optional[float] = Field(None, ge=0.02, le=0.30)
    right_click_cooldown_ms: Optional[float] = Field(None, ge=100.0, le=2000.0)


class CursorPointRequest(BaseModel):
    """Normalized cursor control point with left (L4+L8) and right (L4+L12) pinch telemetry."""

    x: float = Field(..., ge=0.0, le=1.0, description="Normalized X coordinate [0.0, 1.0]")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized Y coordinate [0.0, 1.0]")
    timestamp: Optional[float] = Field(None, description="Client capture timestamp in seconds")
    pinch_distance: Optional[float] = Field(None, ge=0.0, le=2.0, description="Normalized distance between thumb tip and index fingertip (L4 to L8)")
    thumb_x: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized thumb tip X coordinate")
    thumb_y: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized thumb tip Y coordinate")
    right_pinch_distance: Optional[float] = Field(None, ge=0.0, le=2.0, description="Normalized distance between thumb tip and middle fingertip (L4 to L12)")
    middle_x: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized middle fingertip X coordinate")
    middle_y: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized middle fingertip Y coordinate")


class MouseStatusResponse(BaseModel):
    """Live mouse controller status and telemetry."""

    enabled: bool = Field(..., description="Whether mouse control is currently enabled")
    state: str = Field(..., description="Current state: 'disabled', 'active', 'waiting_for_hand', 'error'")
    hand_detected: bool = Field(default=False, description="Whether a valid hand is actively detected")
    control_point: Optional[Dict[str, float]] = Field(default=None, description="Latest normalized control point (x, y)")
    cursor_position: Dict[str, int] = Field(default_factory=lambda: {"x": 0, "y": 0}, description="Current desktop cursor pixel coordinates")
    screen_size: Dict[str, int] = Field(default_factory=lambda: {"width": 1920, "height": 1080}, description="Primary desktop display dimensions")
    sensitivity: float = Field(default=1.0, description="Current sensitivity multiplier")
    smoothing_alpha: float = Field(default=0.35, description="Current smoothing alpha")
    active_margin_x: float = Field(default=0.15, description="Horizontal tracking margin")
    active_margin_y: float = Field(default=0.15, description="Vertical tracking margin")
    dead_zone: float = Field(default=0.05, description="Dead zone radius around center")
    last_error: Optional[str] = Field(default=None, description="Last error message, if any")

    # Phase 6B.1 Left Click Telemetry (Thumb + Index, L4 & L8)
    left_click_enabled: bool = Field(default=True, description="Whether gesture-based left click is enabled")
    pinch_distance: Optional[float] = Field(default=None, description="Latest normalized pinch distance (L4 to L8)")
    pinch_state: str = Field(default="idle", description="Pinch state: 'idle', 'pinched', 'cooldown', 'disabled'")
    pinch_activation_threshold: float = Field(default=0.05, description="Pinch activation distance threshold")
    pinch_release_threshold: float = Field(default=0.08, description="Pinch release distance threshold")
    click_cooldown_ms: float = Field(default=400.0, description="Click cooldown duration in ms")
    last_click_time: Optional[float] = Field(default=None, description="Timestamp of the last left click in seconds")
    last_click_position: Optional[Dict[str, int]] = Field(default=None, description="Desktop pixel position of the last left click")
    click_count: int = Field(default=0, description="Total number of left clicks executed in session")

    # Phase 6B.2 Right Click Telemetry (Thumb + Middle, L4 & L12)
    right_click_enabled: bool = Field(default=True, description="Whether gesture-based right click is enabled")
    right_pinch_distance: Optional[float] = Field(default=None, description="Latest normalized right pinch distance (L4 to L12)")
    right_pinch_state: str = Field(default="idle", description="Right pinch state: 'idle', 'pinched', 'cooldown', 'disabled'")
    right_pinch_activation_threshold: float = Field(default=0.05, description="Right pinch activation distance threshold")
    right_pinch_release_threshold: float = Field(default=0.08, description="Right pinch release distance threshold")
    right_click_cooldown_ms: float = Field(default=500.0, description="Right click cooldown duration in ms")
    last_right_click_time: Optional[float] = Field(default=None, description="Timestamp of the last right click in seconds")
    last_right_click_position: Optional[Dict[str, int]] = Field(default=None, description="Desktop pixel position of the last right click")
    right_click_count: int = Field(default=0, description="Total number of right clicks executed in session")

