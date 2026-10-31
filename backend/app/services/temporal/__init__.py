"""
GestureFlow AI - Phase 5 Temporal Gesture Recognition Package.
"""

from app.services.temporal.dataset_temporal import (
    TemporalDatasetService,
    get_temporal_dataset_service,
)
from app.services.temporal.gesture_rules import GestureRuleMatcher
from app.services.temporal.gesture_state_machine import GestureStateMachine
from app.services.temporal.motion_features import MotionFeatureVector
from app.services.temporal.movement_tracker import MovementTracker
from app.services.temporal.sequence_classifier import (
    SequenceMLPBaseline,
    SequencePreprocessor,
)
from app.services.temporal.temporal_buffer import (
    TemporalFrameBuffer,
    TemporalObservation,
)
from app.services.temporal.temporal_config import (
    TEMPORAL_GESTURE_CATALOG,
    TemporalConfig,
)
from app.services.temporal.temporal_engine import (
    TemporalEngine,
    get_temporal_engine,
)

__all__ = [
    "TemporalConfig",
    "TEMPORAL_GESTURE_CATALOG",
    "TemporalObservation",
    "TemporalFrameBuffer",
    "MotionFeatureVector",
    "MovementTracker",
    "GestureRuleMatcher",
    "GestureStateMachine",
    "SequencePreprocessor",
    "SequenceMLPBaseline",
    "TemporalEngine",
    "get_temporal_engine",
    "TemporalDatasetService",
    "get_temporal_dataset_service",
]
