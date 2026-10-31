"""
Configuration constants and parameters for Phase 5 Temporal Gesture Recognition.
"""

from typing import Dict, List
from app.schemas.temporal import TemporalGestureDefinition


class TemporalConfig:
    """Configurable hyperparameters and thresholds for temporal gesture recognition."""

    # --- Buffer & Window Configuration ---
    # Max observations kept in memory per hand
    BUFFER_MAX_SIZE: int = 60
    # Window duration to retain in seconds (default: 1.5s)
    BUFFER_MAX_DURATION_S: float = 1.5
    # Minimum observations required before temporal evaluation
    MIN_OBSERVATIONS_FOR_RECOGNITION: int = 5
    # Max gap between observations before buffer auto-resets (seconds)
    DISCONTINUITY_THRESHOLD_S: float = 0.35

    # --- Movement & Velocity Thresholds ---
    # Minimum speed (normalized units/sec) to transition from IDLE to CANDIDATE/TRACKING
    MOTION_START_SPEED_THRESHOLD: float = 0.15
    # Movement speed considered stationary / resting
    MOTION_STOP_SPEED_THRESHOLD: float = 0.08
    # Minimum displacement (normalized) to qualify as an intentional movement
    MIN_DISPLACEMENT_THRESHOLD: float = 0.10

    # --- Swipe Gesture Thresholds (T001 - T004) ---
    SWIPE_MIN_DISPLACEMENT: float = 0.15          # Normalized screen dimension
    SWIPE_MIN_VELOCITY: float = 0.30              # Normalized units/sec
    SWIPE_MIN_LINEARITY: float = 0.72             # Ratio of net distance to path length
    SWIPE_PRIMARY_AXIS_RATIO: float = 1.6         # Primary axis must dominate secondary axis by 1.6x
    SWIPE_MIN_DURATION_MS: float = 150.0          # Min gesture duration
    SWIPE_MAX_DURATION_MS: float = 900.0          # Max gesture duration

    # --- Wave Gesture Thresholds (T005) ---
    WAVE_MIN_DIRECTION_CHANGES: int = 3           # At least 3 directional reversals (left-right-left or right-left-right)
    WAVE_MIN_PATH_LENGTH: float = 0.35            # Substantial cumulative path traveled
    WAVE_MAX_NET_DISPLACEMENT: float = 0.30       # Remains in general localized area
    WAVE_MIN_DURATION_MS: float = 350.0
    WAVE_MAX_DURATION_MS: float = 1600.0

    # --- Circle Gesture Thresholds (T006) ---
    CIRCLE_MIN_ANGULAR_TRAVERSAL_RAD: float = 4.8 # At least ~275 degrees (close to 2*pi)
    CIRCLE_MIN_RADIUS: float = 0.04               # Minimum radius from centroid
    CIRCLE_CLOSURE_RATIO: float = 0.35            # End point must be within 35% of start relative to radius
    CIRCLE_MIN_DURATION_MS: float = 450.0
    CIRCLE_MAX_DURATION_MS: float = 1800.0

    # --- Push & Pull Gestures (T007, T008) [Experimental] ---
    PUSH_PULL_MIN_SCALE_CHANGE: float = 0.20      # 20% relative palm size change
    PUSH_PULL_MAX_XY_DISPLACEMENT: float = 0.15   # Minimal lateral movement
    PUSH_PULL_MIN_DURATION_MS: float = 200.0
    PUSH_PULL_MAX_DURATION_MS: float = 1000.0

    # --- Double Tap Gesture (T009) [Experimental] ---
    DOUBLE_TAP_MAX_INTERVAL_MS: float = 650.0     # Max interval between two forward taps
    DOUBLE_TAP_MIN_PEAK_VELOCITY: float = 0.25

    # --- State Machine & Cooldown ---
    DEFAULT_COOLDOWN_MS: float = 550.0            # Time to suppress re-triggering same gesture
    MAX_TRACKING_DURATION_MS: float = 2000.0      # Auto-reset if movement exceeds 2 seconds without trigger


# Standard Catalog of Registered Dynamic Gestures
TEMPORAL_GESTURE_CATALOG: Dict[str, TemporalGestureDefinition] = {
    "T001": TemporalGestureDefinition(
        id="T001",
        name="Swipe Left",
        description="Hand moves horizontally to the left across the screen.",
        expected_motion="Horizontal translation -X",
        is_experimental=False,
        min_duration_ms=TemporalConfig.SWIPE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.SWIPE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T002": TemporalGestureDefinition(
        id="T002",
        name="Swipe Right",
        description="Hand moves horizontally to the right across the screen.",
        expected_motion="Horizontal translation +X",
        is_experimental=False,
        min_duration_ms=TemporalConfig.SWIPE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.SWIPE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T003": TemporalGestureDefinition(
        id="T003",
        name="Swipe Up",
        description="Hand moves vertically upward on the screen.",
        expected_motion="Vertical translation -Y",
        is_experimental=False,
        min_duration_ms=TemporalConfig.SWIPE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.SWIPE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T004": TemporalGestureDefinition(
        id="T004",
        name="Swipe Down",
        description="Hand moves vertically downward on the screen.",
        expected_motion="Vertical translation +Y",
        is_experimental=False,
        min_duration_ms=TemporalConfig.SWIPE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.SWIPE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T005": TemporalGestureDefinition(
        id="T005",
        name="Wave",
        description="Hand oscillates back and forth horizontally with multiple direction reversals.",
        expected_motion="Oscillating horizontal trajectory",
        is_experimental=False,
        min_duration_ms=TemporalConfig.WAVE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.WAVE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T006": TemporalGestureDefinition(
        id="T006",
        name="Circle",
        description="Hand traces a circular or elliptical loop.",
        expected_motion="Closed loop angular trajectory",
        is_experimental=False,
        min_duration_ms=TemporalConfig.CIRCLE_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.CIRCLE_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T007": TemporalGestureDefinition(
        id="T007",
        name="Push",
        description="Hand moves forward toward the webcam (palm scale expands).",
        expected_motion="Forward translation -Z / scale expansion",
        is_experimental=True,
        min_duration_ms=TemporalConfig.PUSH_PULL_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.PUSH_PULL_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T008": TemporalGestureDefinition(
        id="T008",
        name="Pull",
        description="Hand retracts away from the webcam (palm scale contracts).",
        expected_motion="Backward translation +Z / scale contraction",
        is_experimental=True,
        min_duration_ms=TemporalConfig.PUSH_PULL_MIN_DURATION_MS,
        max_duration_ms=TemporalConfig.PUSH_PULL_MAX_DURATION_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
    "T009": TemporalGestureDefinition(
        id="T009",
        name="Double Tap",
        description="Two distinct forward tapping motions in quick succession.",
        expected_motion="Two forward velocity pulses",
        is_experimental=True,
        min_duration_ms=250.0,
        max_duration_ms=TemporalConfig.DOUBLE_TAP_MAX_INTERVAL_MS,
        cooldown_ms=TemporalConfig.DEFAULT_COOLDOWN_MS,
    ),
}
