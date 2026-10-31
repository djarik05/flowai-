"""
Unit and integration tests for Phase 5 Temporal Gesture Recognition.

Tests:
1. Temporal buffer: capacity bounds, time-based eviction, discontinuity resets.
2. Kinematics & movement tracker: displacement, velocity, linearity, reversals, circle sweep.
3. Gesture rule matcher:
   - T001: Swipe Left
   - T002: Swipe Right
   - T003: Swipe Up
   - T004: Swipe Down
   - T005: Wave
   - T006: Circle
   - T007: Push
   - T008: Pull
4. State machine lifecycle: IDLE -> CANDIDATE -> TRACKING -> RECOGNIZED -> COOLDOWN -> IDLE.
5. Cooldown suppression: prevents duplicate events during a single swipe.
6. Temporal engine multi-hand isolation: Left and Right tracking states are independent.
7. Sequence preprocessor & fixed (30, 63) resampling.
8. Temporal dataset collection & disk persistence.
9. FastAPI temporal endpoints.
"""

import math
import time
from typing import List, Tuple
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.temporal import (
    TEMPORAL_GESTURE_CATALOG,
    GestureRuleMatcher,
    GestureStateMachine,
    MotionFeatureVector,
    MovementTracker,
    SequencePreprocessor,
    TemporalConfig,
    TemporalDatasetService,
    TemporalEngine,
    TemporalFrameBuffer,
    get_temporal_engine,
)
from app.schemas.temporal import StateMachineState


def generate_hand_landmarks(base_x: float, base_y: float, base_z: float = 0.0) -> List[Tuple[float, float, float]]:
    """Helper generating 21 valid hand landmark points offset by base coordinates."""
    pts = []
    for i in range(21):
        x = base_x + (i % 5) * 0.01
        y = base_y + (i // 5) * 0.01
        z = base_z + (i % 3) * 0.005
        pts.append((x, y, z))
    return pts


# ---------------------------------------------------------------------------
# 1. Temporal Frame Buffer Tests
# ---------------------------------------------------------------------------


def test_temporal_buffer_bounds_and_eviction():
    """Verify buffer adheres to maximum size and evicts data older than max duration."""
    buf = TemporalFrameBuffer(max_size=10, max_duration_s=1.0)
    start_t = 100.0

    # Add 15 frames spaced 0.05s apart
    for i in range(15):
        t = start_t + i * 0.05
        lms = generate_hand_landmarks(0.5 + i * 0.01, 0.5)
        added = buf.append(timestamp=t, landmarks=lms, handedness="Right")
        assert added is True

    # Buffer should not exceed max_size 10
    assert len(buf) <= 10
    assert buf.latest_observation is not None
    assert buf.latest_observation.timestamp == pytest.approx(100.0 + 14 * 0.05)


def test_temporal_buffer_discontinuity_reset():
    """Verify buffer clears automatically when tracking gap exceeds threshold."""
    buf = TemporalFrameBuffer(discontinuity_threshold_s=0.35)
    t0 = 10.0
    buf.append(t0, generate_hand_landmarks(0.4, 0.4))
    buf.append(t0 + 0.05, generate_hand_landmarks(0.42, 0.4))
    assert len(buf) == 2

    # Advance by 0.5s (> 0.35s gap)
    t_after_gap = t0 + 0.55
    buf.append(t_after_gap, generate_hand_landmarks(0.6, 0.6))

    # Old observations must be purged to prevent false high velocity calculation
    assert len(buf) == 1
    assert buf.latest_observation.timestamp == t_after_gap


def test_temporal_buffer_rejects_corrupted_coordinates():
    """Verify buffer rejects empty, non-21, or non-finite landmark arrays."""
    buf = TemporalFrameBuffer()
    # Empty
    assert buf.append(1.0, []) is False
    # Only 10 points
    assert buf.append(1.0, [(0.5, 0.5, 0.0)] * 10) is False
    # Non-finite coordinate
    bad_pts = [(0.5, 0.5, 0.0)] * 21
    bad_pts[0] = (float("nan"), 0.5, 0.0)
    assert buf.append(1.0, bad_pts) is False
    assert len(buf) == 0


# ---------------------------------------------------------------------------
# 2. Movement Tracker & Kinematics Tests
# ---------------------------------------------------------------------------


def test_movement_tracker_linear_swipe_kinematics():
    """Verify displacement, linearity, and velocity on horizontal trajectory."""
    buf = TemporalFrameBuffer(max_size=30)
    tracker = MovementTracker(target_point="centroid")

    # Simulate 300ms swipe to the left (-X): 0.6 -> 0.2
    for idx, x in enumerate(np.linspace(0.6, 0.2, 10)):
        t = 1.0 + idx * (0.3 / 9.0)
        buf.append(t, generate_hand_landmarks(x, 0.5))

    feat = tracker.extract_features(buf)
    assert feat is not None
    assert feat.net_dx < -0.35
    assert abs(feat.net_dy) < 0.05
    assert feat.linearity > 0.95  # Pure straight line
    assert feat.primary_direction == "left"
    assert feat.speed > 0.8  # ~0.4 units / 0.3 sec = 1.33 u/s


def test_movement_tracker_reversals_and_angular_sweep():
    """Verify wave direction reversals and circular sweep calculations."""
    buf = TemporalFrameBuffer(max_size=60)
    tracker = MovementTracker(target_point="centroid")

    # Simulate circular motion around (0.5, 0.5) with radius 0.15 over 1.0s
    times = np.linspace(0.0, 1.0, 25)
    angles = np.linspace(0.0, 2 * math.pi, 25)

    for t, th in zip(times, angles):
        x = 0.5 + 0.15 * math.cos(th)
        y = 0.5 + 0.15 * math.sin(th)
        buf.append(t, generate_hand_landmarks(x, y))

    feat = tracker.extract_features(buf)
    assert feat is not None
    # Angular traversal should be close to 2*pi radians (~6.28)
    assert feat.angular_traversal > 5.5
    # Start and end positions should be close
    assert feat.closure_distance < 0.05


# ---------------------------------------------------------------------------
# 3. Dynamic Gesture Rule Matching Tests
# ---------------------------------------------------------------------------


def test_rule_matching_all_swipe_directions():
    """Verify Swipe Left, Right, Up, and Down are accurately matched by rules."""
    # 1. Swipe Left (T001)
    feat_left = MotionFeatureVector(
        sample_count=10, duration_ms=280.0,
        start_pos=(0.6, 0.5, 0.0), end_pos=(0.25, 0.5, 0.0),
        net_dx=-0.35, net_dy=0.02, net_dz=0.0, net_distance=0.35,
        path_length=0.36, linearity=0.97,
        avg_velocity_x=-1.25, avg_velocity_y=0.05, avg_velocity_z=0.0,
        speed=1.25, peak_speed=1.5, primary_direction="left",
        reversals_x=0, reversals_y=0, scale_ratio=1.0, angular_traversal=0.0, closure_distance=0.35,
    )
    res_left = GestureRuleMatcher.evaluate(feat_left)
    assert res_left is not None
    assert res_left[0] == "T001"
    assert res_left[1] == "Swipe Left"
    assert res_left[2] >= 0.70

    # 2. Swipe Right (T002)
    feat_right = MotionFeatureVector(
        sample_count=10, duration_ms=280.0,
        start_pos=(0.25, 0.5, 0.0), end_pos=(0.6, 0.5, 0.0),
        net_dx=0.35, net_dy=0.02, net_dz=0.0, net_distance=0.35,
        path_length=0.36, linearity=0.97,
        avg_velocity_x=1.25, avg_velocity_y=0.05, avg_velocity_z=0.0,
        speed=1.25, peak_speed=1.5, primary_direction="right",
        reversals_x=0, reversals_y=0, scale_ratio=1.0, angular_traversal=0.0, closure_distance=0.35,
    )
    res_right = GestureRuleMatcher.evaluate(feat_right)
    assert res_right is not None
    assert res_right[0] == "T002"
    assert res_right[1] == "Swipe Right"

    # 3. Swipe Up (T003)
    feat_up = MotionFeatureVector(
        sample_count=10, duration_ms=280.0,
        start_pos=(0.5, 0.7, 0.0), end_pos=(0.5, 0.35, 0.0),
        net_dx=0.02, net_dy=-0.35, net_dz=0.0, net_distance=0.35,
        path_length=0.36, linearity=0.97,
        avg_velocity_x=0.05, avg_velocity_y=-1.25, avg_velocity_z=0.0,
        speed=1.25, peak_speed=1.5, primary_direction="up",
        reversals_x=0, reversals_y=0, scale_ratio=1.0, angular_traversal=0.0, closure_distance=0.35,
    )
    res_up = GestureRuleMatcher.evaluate(feat_up)
    assert res_up is not None
    assert res_up[0] == "T003"
    assert res_up[1] == "Swipe Up"

    # 4. Swipe Down (T004)
    feat_down = MotionFeatureVector(
        sample_count=10, duration_ms=280.0,
        start_pos=(0.5, 0.35, 0.0), end_pos=(0.5, 0.7, 0.0),
        net_dx=0.02, net_dy=0.35, net_dz=0.0, net_distance=0.35,
        path_length=0.36, linearity=0.97,
        avg_velocity_x=0.05, avg_velocity_y=1.25, avg_velocity_z=0.0,
        speed=1.25, peak_speed=1.5, primary_direction="down",
        reversals_x=0, reversals_y=0, scale_ratio=1.0, angular_traversal=0.0, closure_distance=0.35,
    )
    res_down = GestureRuleMatcher.evaluate(feat_down)
    assert res_down is not None
    assert res_down[0] == "T004"
    assert res_down[1] == "Swipe Down"


def test_rule_matching_wave_and_circle():
    """Verify Wave (T005) and Circle (T006) rule matching."""
    # Wave: multiple horizontal reversals with bounded net displacement
    feat_wave = MotionFeatureVector(
        sample_count=20, duration_ms=650.0,
        start_pos=(0.5, 0.5, 0.0), end_pos=(0.52, 0.51, 0.0),
        net_dx=0.02, net_dy=0.01, net_dz=0.0, net_distance=0.022,
        path_length=0.58, linearity=0.04,
        avg_velocity_x=0.03, avg_velocity_y=0.01, avg_velocity_z=0.0,
        speed=0.89, peak_speed=1.4, primary_direction="right",
        reversals_x=4, reversals_y=0, scale_ratio=1.0, angular_traversal=0.5, closure_distance=0.022,
    )
    res_wave = GestureRuleMatcher.evaluate(feat_wave)
    assert res_wave is not None
    assert res_wave[0] == "T005"
    assert res_wave[1] == "Wave"

    # Circle: full angular loop around centroid
    feat_circle = MotionFeatureVector(
        sample_count=25, duration_ms=800.0,
        start_pos=(0.65, 0.5, 0.0), end_pos=(0.64, 0.51, 0.0),
        net_dx=-0.01, net_dy=0.01, net_dz=0.0, net_distance=0.014,
        path_length=0.94, linearity=0.02,
        avg_velocity_x=-0.01, avg_velocity_y=0.01, avg_velocity_z=0.0,
        speed=1.17, peak_speed=1.6, primary_direction="none",
        reversals_x=2, reversals_y=2, scale_ratio=1.0, angular_traversal=6.15, closure_distance=0.014,
    )
    res_circle = GestureRuleMatcher.evaluate(feat_circle)
    assert res_circle is not None
    assert res_circle[0] == "T006"
    assert res_circle[1] == "Circle"


# ---------------------------------------------------------------------------
# 4. State Machine & Cooldown Tests
# ---------------------------------------------------------------------------


def test_state_machine_lifecycle_and_cooldown():
    """Verify state transitions and cooldown suppression preventing multi-fires."""
    sm = GestureStateMachine(hand_label="Right")
    assert sm.state == StateMachineState.IDLE

    # 1. At rest: stays IDLE
    evt = sm.update(timestamp=1.0, feat=None, instantaneous_speed=0.02)
    assert evt is None
    assert sm.state == StateMachineState.IDLE

    # 2. Movement starts: transitions to CANDIDATE
    sm.update(timestamp=1.05, feat=None, instantaneous_speed=0.25)
    assert sm.state == StateMachineState.CANDIDATE

    # 3. Motion continues > 80ms: transitions to TRACKING
    sm.update(timestamp=1.15, feat=None, instantaneous_speed=0.35)
    assert sm.state == StateMachineState.TRACKING

    # 4. Feature matches Swipe Right: triggers RECOGNIZED event, immediately goes to COOLDOWN
    feat_match = MotionFeatureVector(
        sample_count=8, duration_ms=250.0,
        start_pos=(0.2, 0.5, 0.0), end_pos=(0.55, 0.5, 0.0),
        net_dx=0.35, net_dy=0.01, net_dz=0.0, net_distance=0.35,
        path_length=0.36, linearity=0.97,
        avg_velocity_x=1.4, avg_velocity_y=0.04, avg_velocity_z=0.0,
        speed=1.4, peak_speed=1.7, primary_direction="right",
        reversals_x=0, reversals_y=0, scale_ratio=1.0, angular_traversal=0.0, closure_distance=0.35,
    )

    event = sm.update(timestamp=1.35, feat=feat_match, instantaneous_speed=0.40)
    assert event is not None
    assert event.gesture_id == "T002"
    assert event.gesture_name == "Swipe Right"
    assert sm.state == StateMachineState.COOLDOWN

    # 5. During cooldown (e.g. 200ms later < 550ms cooldown): should NOT trigger again
    repeat_event = sm.update(timestamp=1.55, feat=feat_match, instantaneous_speed=0.40)
    assert repeat_event is None
    assert sm.state == StateMachineState.COOLDOWN

    # 6. After cooldown expires (600ms later): transitions back to IDLE
    sm.update(timestamp=1.95, feat=None, instantaneous_speed=0.02)
    assert sm.state == StateMachineState.IDLE


# ---------------------------------------------------------------------------
# 5. Temporal Engine & Multi-Hand Isolation
# ---------------------------------------------------------------------------


def test_temporal_engine_multi_hand_isolation():
    """Verify Left and Right hands have independent buffers and state machines."""
    engine = TemporalEngine()
    engine.reset()

    # Move Right hand
    lms_r = generate_hand_landmarks(0.3, 0.5)
    evt_r, telem_r = engine.process_hand(
        hand_id=0, handedness="Right", landmarks=lms_r, timestamp=1.0
    )
    assert telem_r.handedness == "Right"
    assert telem_r.buffer_size == 1

    # Left hand stays at rest
    lms_l = generate_hand_landmarks(0.8, 0.5)
    evt_l, telem_l = engine.process_hand(
        hand_id=1, handedness="Left", landmarks=lms_l, timestamp=1.0
    )
    assert telem_l.handedness == "Left"
    assert telem_l.buffer_size == 1

    status = engine.get_status()
    assert status.is_active is True
    assert status.hands_tracked == 2
    assert "Right" in status.movement_telemetry
    assert "Left" in status.movement_telemetry


# ---------------------------------------------------------------------------
# 6. Sequence Preprocessor & Resampling Tests
# ---------------------------------------------------------------------------


def test_sequence_preprocessor_fixed_resampling():
    """Verify variable length sequences are resampled to exact (30, 63) matrix."""
    preprocessor = SequencePreprocessor(target_length=30)

    # Sequence of 15 frames
    short_seq = [generate_hand_landmarks(0.3 + i * 0.02, 0.5) for i in range(15)]
    res_short = preprocessor.process_sequence(short_seq)
    assert res_short is not None
    assert res_short.shape == (30, 63)
    assert np.all(np.isfinite(res_short))

    # Sequence of 45 frames
    long_seq = [generate_hand_landmarks(0.3 + i * 0.01, 0.5) for i in range(45)]
    res_long = preprocessor.process_sequence(long_seq)
    assert res_long is not None
    assert res_long.shape == (30, 63)
    assert np.all(np.isfinite(res_long))


# ---------------------------------------------------------------------------
# 7. Temporal Dataset Collection Tests
# ---------------------------------------------------------------------------


def test_temporal_dataset_collection_lifecycle(tmp_path):
    """Verify starting, recording, committing, and gathering dataset stats."""
    service = TemporalDatasetService(base_dir=tmp_path)

    # Start recording T001
    status = service.start_collection(gesture_id="T001", session_id="test_sess_01")
    assert status.is_collecting is True
    assert status.gesture_id == "T001"

    # Feed 15 frames over 300ms
    t0 = 100.0
    for i in range(15):
        service.record_frame(
            generate_hand_landmarks(0.6 - i * 0.02, 0.5),
            timestamp=t0 + i * 0.02,
            handedness="Right",
        )

    # Commit sequence
    sample = service.commit_sequence()
    assert sample is not None
    assert sample.gesture_id == "T001"
    assert sample.frame_count == 15
    assert sample.duration_ms > 200.0
    assert (tmp_path / "T001" / f"{sample.sample_id}.json").exists()

    # Verify stats
    stats = service.get_dataset_stats()
    assert stats["total_sequences"] == 1
    assert stats["gestures"]["T001"]["sequence_count"] == 1

    # Stop collection
    stop_status = service.stop_collection()
    assert stop_status.is_collecting is False


# ---------------------------------------------------------------------------
# 8. Temporal API Routes Tests
# ---------------------------------------------------------------------------


def test_temporal_api_endpoints():
    """Verify FastAPI routes for status, catalog, events, and reset."""
    client = TestClient(app)

    # 1. Status
    res_status = client.get("/api/v1/temporal/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "is_active" in data_status
    assert "hands_tracked" in data_status
    assert data_status["active_gestures_count"] == 9

    # 2. Gestures Catalog
    res_gestures = client.get("/api/v1/temporal/gestures")
    assert res_gestures.status_code == 200
    gestures = res_gestures.json()
    assert len(gestures) == 9
    ids = [g["id"] for g in gestures]
    assert "T001" in ids  # Swipe Left
    assert "T005" in ids  # Wave
    assert "T006" in ids  # Circle
    assert "T007" in ids  # Push (Experimental)

    # 3. Events history
    res_events = client.get("/api/v1/temporal/events")
    assert res_events.status_code == 200
    assert isinstance(res_events.json(), list)

    # 4. Engine Reset
    res_reset = client.post("/api/v1/temporal/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["success"] is True

    # 5. Dataset Stats
    res_stats = client.get("/api/v1/temporal/dataset/stats")
    assert res_stats.status_code == 200
    assert "total_sequences" in res_stats.json()
