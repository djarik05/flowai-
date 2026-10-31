"""
Master coordinator engine for Phase 5 Temporal Gesture Recognition.
"""

from collections import deque
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.temporal import (
    MovementTelemetry,
    StateMachineState,
    TemporalEngineStatusResponse,
    TemporalGestureEvent,
)
from app.services.temporal.gesture_state_machine import GestureStateMachine
from app.services.temporal.motion_features import MotionFeatureVector
from app.services.temporal.movement_tracker import MovementTracker
from app.services.temporal.temporal_buffer import TemporalFrameBuffer
from app.services.temporal.temporal_config import TEMPORAL_GESTURE_CATALOG, TemporalConfig


class TemporalEngine:
    """
    Coordinates multi-hand temporal buffers, movement tracking, rule matching,
    and state machines to detect dynamic gestures in real time.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._is_active = True

        # Per-handedness components: {"Right": ..., "Left": ...}
        self._buffers: Dict[str, TemporalFrameBuffer] = {
            "Right": TemporalFrameBuffer(),
            "Left": TemporalFrameBuffer(),
        }
        self._trackers: Dict[str, MovementTracker] = {
            "Right": MovementTracker(target_point="centroid"),
            "Left": MovementTracker(target_point="centroid"),
        }
        self._state_machines: Dict[str, GestureStateMachine] = {
            "Right": GestureStateMachine(hand_label="Right"),
            "Left": GestureStateMachine(hand_label="Left"),
        }

        # Event history (ring buffer of last 50 events)
        self._recent_events: deque[TemporalGestureEvent] = deque(maxlen=50)
        self._total_events_recognized = 0

        # Telemetry & performance metrics
        self._telemetry: Dict[str, MovementTelemetry] = {}
        self._last_processed_time: float = 0.0
        self._total_latency_ms: float = 0.0
        self._frame_count: int = 0

    def process_hand(
        self,
        hand_id: int,
        handedness: str,
        landmarks: Any,
        timestamp: float,
        static_gesture_id: Optional[str] = None,
        static_gesture_name: Optional[str] = None,
    ) -> Tuple[Optional[TemporalGestureEvent], MovementTelemetry]:
        """
        Process a single detected hand observation.

        Returns:
            (event, telemetry)
        """
        t0 = time.perf_counter()
        label = handedness if handedness in ("Right", "Left") else ("Right" if hand_id == 0 else "Left")

        with self._lock:
            buf = self._buffers[label]
            tracker = self._trackers[label]
            sm = self._state_machines[label]

            # 1. Append observation to buffer
            buf.append(
                timestamp=timestamp,
                landmarks=landmarks,
                handedness=label,
                static_gesture_id=static_gesture_id,
                static_gesture_name=static_gesture_name,
            )

            # 2. Extract kinematics and instantaneous speed
            vx, vy, vz, speed = tracker.compute_instantaneous_velocity(buf, num_frames=4)
            feat = tracker.extract_features(buf, duration_s=1.2)

            # 3. Update state machine
            event = sm.update(timestamp=timestamp, feat=feat, instantaneous_speed=speed)
            if event:
                self._recent_events.append(event)
                self._total_events_recognized += 1

            # 4. Compile telemetry
            latest_obs = buf.latest_observation
            curr_pos = (
                {"x": latest_obs.centroid[0], "y": latest_obs.centroid[1], "z": latest_obs.centroid[2]}
                if latest_obs
                else {"x": 0.0, "y": 0.0, "z": 0.0}
            )

            telem = MovementTelemetry(
                hand_id=hand_id,
                handedness=label,
                state=sm.state,
                current_position=curr_pos,
                velocity={"vx": round(vx, 3), "vy": round(vy, 3), "vz": round(vz, 3), "speed": round(speed, 3)},
                direction=feat.primary_direction if feat else "none",
                linearity=feat.linearity if feat else 1.0,
                path_length=feat.path_length if feat else 0.0,
                buffer_size=len(buf),
                duration_ms=feat.duration_ms if feat else 0.0,
            )
            self._telemetry[label] = telem

            t1 = time.perf_counter()
            latency = (t1 - t0) * 1000.0
            self._total_latency_ms += latency
            self._frame_count += 1
            self._last_processed_time = timestamp

            return event, telem

    def process_no_hands(self, timestamp: float) -> None:
        """Handle tracking loss when no hands are in the camera frame."""
        with self._lock:
            # If tracking was inactive for > discontinuity threshold, reset buffers & state machines
            if self._last_processed_time > 0 and (timestamp - self._last_processed_time > TemporalConfig.DISCONTINUITY_THRESHOLD_S):
                self._reset_internal()
            self._last_processed_time = timestamp

    def get_status(self) -> TemporalEngineStatusResponse:
        """Retrieve complete status and performance telemetry."""
        with self._lock:
            avg_lat = (self._total_latency_ms / max(1, self._frame_count)) if self._frame_count > 0 else 0.0
            active_hands = sum(1 for b in self._buffers.values() if len(b) > 0)

            return TemporalEngineStatusResponse(
                is_active=self._is_active,
                hands_tracked=active_hands,
                active_gestures_count=len(TEMPORAL_GESTURE_CATALOG),
                total_events_recognized=self._total_events_recognized,
                recent_events=list(self._recent_events),
                movement_telemetry=dict(self._telemetry),
                avg_processing_latency_ms=round(avg_lat, 4),
            )

    def get_recent_events(self, limit: int = 20) -> List[TemporalGestureEvent]:
        """Return recent temporal gesture events."""
        with self._lock:
            events = list(self._recent_events)
            return events[-limit:]

    def reset(self) -> None:
        """Manually reset all buffers and state machines."""
        with self._lock:
            self._reset_internal()

    def _reset_internal(self) -> None:
        for b in self._buffers.values():
            b.clear()
        for sm in self._state_machines.values():
            sm.reset()
        for label in self._telemetry:
            self._telemetry[label].state = StateMachineState.IDLE
            self._telemetry[label].buffer_size = 0


# Singleton instance accessor
_temporal_engine: Optional[TemporalEngine] = None
_engine_lock = threading.Lock()


def get_temporal_engine() -> TemporalEngine:
    global _temporal_engine
    if _temporal_engine is None:
        with _engine_lock:
            if _temporal_engine is None:
                _temporal_engine = TemporalEngine()
    return _temporal_engine
