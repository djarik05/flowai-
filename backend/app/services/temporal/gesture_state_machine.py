"""
Finite State Machine governing temporal gesture candidate detection, tracking, and cooldown.
"""

import time
import uuid
from typing import Optional, Tuple
from app.schemas.temporal import StateMachineState, TemporalGestureEvent
from app.services.temporal.gesture_rules import GestureRuleMatcher
from app.services.temporal.motion_features import MotionFeatureVector
from app.services.temporal.temporal_config import TemporalConfig


class GestureStateMachine:
    """
    Manages state transitions for a single tracked hand:
    IDLE -> CANDIDATE -> TRACKING -> RECOGNIZED -> COOLDOWN -> IDLE
    """

    def __init__(self, hand_label: str = "Right"):
        self.hand_label = hand_label
        self._state = StateMachineState.IDLE
        self._state_entry_time = time.time()
        self._last_recognized_id: Optional[str] = None
        self._last_event: Optional[TemporalGestureEvent] = None
        self._candidate_start_time: float = 0.0

    @property
    def state(self) -> StateMachineState:
        return self._state

    def update(
        self,
        timestamp: float,
        feat: Optional[MotionFeatureVector],
        instantaneous_speed: float,
    ) -> Optional[TemporalGestureEvent]:
        """
        Advance state machine according to current kinematics and motion features.
        Returns:
            TemporalGestureEvent if a gesture is recognized on this frame, else None.
        """
        now = timestamp

        # Handle COOLDOWN state
        if self._state == StateMachineState.COOLDOWN:
            elapsed_cooldown = (now - self._state_entry_time) * 1000.0
            if elapsed_cooldown >= TemporalConfig.DEFAULT_COOLDOWN_MS:
                self._transition_to(StateMachineState.IDLE, now)
            else:
                return None

        # 1. State: IDLE
        if self._state == StateMachineState.IDLE:
            if instantaneous_speed >= TemporalConfig.MOTION_START_SPEED_THRESHOLD:
                self._candidate_start_time = now
                self._transition_to(StateMachineState.CANDIDATE, now)
            return None

        # 2. State: CANDIDATE
        if self._state == StateMachineState.CANDIDATE:
            candidate_duration = (now - self._candidate_start_time) * 1000.0
            if candidate_duration >= 80.0:  # Confirmed intentional motion
                self._transition_to(StateMachineState.TRACKING, now)
            elif instantaneous_speed < TemporalConfig.MOTION_STOP_SPEED_THRESHOLD:
                self._transition_to(StateMachineState.IDLE, now)
            return None

        # If no valid motion features yet during TRACKING
        if feat is None:
            self._transition_to(StateMachineState.IDLE, now)
            return None

        # 3. State: TRACKING
        if self._state == StateMachineState.TRACKING:
            # Check maximum duration timeout (prevent getting stuck in tracking)
            if feat.duration_ms > TemporalConfig.MAX_TRACKING_DURATION_MS:
                self._transition_to(StateMachineState.IDLE, now)
                return None

            # Evaluate rules against accumulated motion features
            match_res = GestureRuleMatcher.evaluate(feat)
            if match_res is not None:
                gesture_id, gesture_name, confidence = match_res

                event = TemporalGestureEvent(
                    event_id=f"evt_{int(now*1000)}_{uuid.uuid4().hex[:6]}",
                    gesture_id=gesture_id,
                    gesture_name=gesture_name,
                    confidence=confidence,
                    status="recognized",
                    timestamp=now,
                    handedness=self.hand_label,
                    duration_ms=round(feat.duration_ms, 1),
                    velocity=round(feat.speed, 3),
                    direction=feat.primary_direction,
                    displacement={
                        "dx": round(feat.net_dx, 4),
                        "dy": round(feat.net_dy, 4),
                        "dz": round(feat.net_dz, 4),
                    },
                )

                self._last_event = event
                self._last_recognized_id = gesture_id
                self._transition_to(StateMachineState.RECOGNIZED, now)
                # Immediately move to COOLDOWN to prevent multi-fire on same swipe
                self._transition_to(StateMachineState.COOLDOWN, now)
                return event

            # If movement ceased without matching any gesture
            if instantaneous_speed < TemporalConfig.MOTION_STOP_SPEED_THRESHOLD and feat.duration_ms > 350.0:
                self._transition_to(StateMachineState.IDLE, now)

            return None

        return None

    def reset(self) -> None:
        """Reset state machine to IDLE."""
        self._state = StateMachineState.IDLE
        self._state_entry_time = time.time()
        self._candidate_start_time = 0.0

    def _transition_to(self, new_state: StateMachineState, timestamp: float) -> None:
        self._state = new_state
        self._state_entry_time = timestamp
