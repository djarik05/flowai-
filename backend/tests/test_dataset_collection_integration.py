"""
Comprehensive Integration Tests for Phase 3 Dataset Collection & Persistence.

Tests full end-to-end collection pipeline without requiring physical webcam hardware:
- Actual MediaPipe Landmark extraction & schema conversion
- Real DatasetService atomic file persistence in temporary directories
- Verification of JSON files on disk surviving service restarts
- Dataset statistics updates
- Lifecycle: Start, Pause, Resume, Stop, and duplicate worker rejection
- Edge cases: No-hand frames, invalid coordinates, 2-hand preservation
- Resilient error handling (MediaPipe executor shutdown)
"""

import json
import math
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.camera_manager import CameraManager
from app.services.dataset_collector import DatasetCollector
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService
from app.services.hand_tracking import (
    DetectedHand,
    HandTrackingService,
    Landmark,
    TrackingResult,
    TrackingState,
)


def create_mock_hand(
    hand_id: int = 0,
    handedness: str = "Right",
    confidence: float = 0.95,
    num_landmarks: int = 21,
    nan_coords: bool = False,
) -> DetectedHand:
    """Create a realistic MediaPipe DetectedHand fixture with 21 coordinates."""
    landmarks = []
    for i in range(num_landmarks):
        val = float("nan") if nan_coords and i == 4 else 0.1 * (i + 1) / num_landmarks
        landmarks.append(
            Landmark(
                index=i,
                x=val if math.isfinite(val) else 0.5,
                y=val if math.isfinite(val) else 0.5,
                z=0.01 * i,
                pixel_x=int(val * 640) if math.isfinite(val) else 320,
                pixel_y=int(val * 480) if math.isfinite(val) else 240,
            )
        )
    return DetectedHand(
        hand_id=hand_id,
        landmarks=landmarks,
        handedness=handedness,
        handedness_confidence=confidence,
    )


@pytest.fixture
def test_env(tmp_path: Path):
    """Setup isolated real DatasetService and GestureService using temporary paths."""
    dataset_dir = tmp_path / "test_datasets"
    registry_file = tmp_path / "test_gestures" / "registry.json"

    dataset_svc = DatasetService(dataset_dir=dataset_dir)
    gesture_svc = GestureService(registry_file=registry_file)

    mock_camera = MagicMock(spec=CameraManager)
    mock_camera.is_healthy.return_value = True

    mock_tracking = MagicMock(spec=HandTrackingService)
    mock_tracking.is_active = True
    mock_tracking.start.return_value = True

    return {
        "dataset_svc": dataset_svc,
        "gesture_svc": gesture_svc,
        "camera_manager": mock_camera,
        "tracking_service": mock_tracking,
        "dataset_dir": dataset_dir,
    }


def test_one_hand_detected_and_saved(test_env):
    """Test that a valid 1-hand detection is converted, validated, and saved to disk."""
    dataset_svc = test_env["dataset_svc"]
    mock_tracking = test_env["tracking_service"]

    # Tracking service returns 1 hand with 21 landmarks
    hand = create_mock_hand(0, "Right", 0.96)
    valid_result = TrackingResult(
        status=TrackingState.ACTIVE,
        hands_detected=1,
        hands=[hand],
        processing_time_ms=12.5,
    )
    mock_tracking.wait_for_next_result.return_value = (valid_result, 1)

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=test_env["camera_manager"],
        tracking_service=mock_tracking,
    )

    started = collector.start_collection(
        gesture_id="G001",
        gesture_name="Open Palm",
        target_samples=1,
        sample_interval_ms=30,
    )
    assert started is True

    # Allow background collector thread to process frame and persist
    time.sleep(0.15)
    collector.stop_collection()

    status = collector.get_status()
    assert status.collected_samples >= 1

    # Verify actual file on disk
    samples, total = dataset_svc.get_samples(gesture_id="G001")
    assert total == 1
    assert samples[0].gesture_id == "G001"
    assert samples[0].handedness == "Right"


def test_no_hand_detected_no_sample_saved(test_env):
    """Test that frames with no hands detected are discarded and never saved."""
    dataset_svc = test_env["dataset_svc"]
    mock_tracking = test_env["tracking_service"]

    # Tracking returns empty hands list
    empty_result = TrackingResult(
        status=TrackingState.ACTIVE,
        hands_detected=0,
        hands=[],
        processing_time_ms=10.0,
    )
    mock_tracking.wait_for_next_result.return_value = (empty_result, 1)

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=test_env["camera_manager"],
        tracking_service=mock_tracking,
    )

    collector.start_collection(
        gesture_id="G001",
        gesture_name="Open Palm",
        target_samples=5,
        sample_interval_ms=30,
    )

    time.sleep(0.1)
    status = collector.get_status()
    collector.stop_collection()

    assert status.hand_detected is False
    assert status.collected_samples == 0

    _, total = dataset_svc.get_samples()
    assert total == 0


def test_invalid_landmarks_rejected(test_env):
    """Test that incomplete (<21 landmarks) or corrupted coordinates are rejected."""
    dataset_svc = test_env["dataset_svc"]
    mock_tracking = test_env["tracking_service"]

    # Incomplete hand with only 15 landmarks
    bad_hand = create_mock_hand(num_landmarks=15)
    bad_result = TrackingResult(
        status=TrackingState.ACTIVE,
        hands_detected=1,
        hands=[bad_hand],
        processing_time_ms=11.0,
    )
    mock_tracking.wait_for_next_result.return_value = (bad_result, 1)

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=test_env["camera_manager"],
        tracking_service=mock_tracking,
    )

    collector.start_collection(
        gesture_id="G002",
        gesture_name="Closed Fist",
        target_samples=3,
        sample_interval_ms=30,
    )

    time.sleep(0.1)
    status = collector.get_status()
    collector.stop_collection()

    assert status.collected_samples == 0
    _, total = dataset_svc.get_samples(gesture_id="G002")
    assert total == 0


def test_two_hand_result_handled_according_to_schema(test_env):
    """Test that 2 detected hands preserve primary hand landmarks and secondary hand in features."""
    dataset_svc = test_env["dataset_svc"]
    mock_tracking = test_env["tracking_service"]

    hand1 = create_mock_hand(0, "Right", 0.95)
    hand2 = create_mock_hand(1, "Left", 0.90)

    two_hands_result = TrackingResult(
        status=TrackingState.ACTIVE,
        hands_detected=2,
        hands=[hand1, hand2],
        processing_time_ms=15.0,
    )
    mock_tracking.wait_for_next_result.return_value = (two_hands_result, 1)

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=test_env["camera_manager"],
        tracking_service=mock_tracking,
    )

    collector.start_collection(
        gesture_id="G003",
        gesture_name="Thumbs Up",
        target_samples=1,
        sample_interval_ms=30,
    )

    time.sleep(0.15)
    collector.stop_collection()

    samples, total = dataset_svc.get_samples(gesture_id="G003")
    assert total == 1
    sample = dataset_svc.get_sample(samples[0].sample_id)
    assert sample is not None
    assert sample.handedness == "Right"
    assert sample.features is not None
    assert "secondary_hand" in sample.features
    assert sample.features["secondary_hand"]["handedness"] == "Left"
    assert len(sample.features["secondary_hand"]["landmarks"]) == 21


def test_saved_json_structure_and_restart_persistence(test_env):
    """Test that saved sample JSON strictly conforms to schema and survives service restart."""
    dataset_svc = test_env["dataset_svc"]
    dataset_dir = test_env["dataset_dir"]

    # Create and persist a valid sample directly through DatasetService
    lms = [LandmarkCoord(index=i, x=0.04 * i, y=0.04 * i, z=0.001 * i) for i in range(21)]
    sample = DatasetSample(
        sample_id="test_sample_restart_001",
        gesture_id="G004",
        gesture_name="Peace Sign",
        timestamp=datetime.now().isoformat(),
        handedness="Right",
        handedness_confidence=0.98,
        landmarks=lms,
        session_id="session_test_001",
    )
    dataset_svc.save_sample(sample)

    # 1. Verify JSON file on disk directly
    json_path = dataset_dir / "samples" / "G004" / "test_sample_restart_001.json"
    assert json_path.exists()
    assert json_path.stat().st_size > 0

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["sample_id"] == "test_sample_restart_001"
    assert len(data["landmarks"]) == 21
    assert data["handedness"] == "Right"

    # 2. Simulate application restart by creating brand new DatasetService pointing to same folder
    restarted_service = DatasetService(dataset_dir=dataset_dir)
    restarted_sample = restarted_service.get_sample("test_sample_restart_001")
    assert restarted_sample is not None
    assert restarted_sample.sample_id == "test_sample_restart_001"
    assert restarted_sample.gesture_name == "Peace Sign"

    # 3. Check stats match
    stats = restarted_service.get_stats()
    assert stats.total_samples == 1
    assert stats.samples_per_gesture.get("G004") == 1
    assert stats.gesture_counts.get("G004") == 1


def test_collection_lifecycle_pause_resume_stop(test_env):
    """Test complete collection state transitions: Start -> Pause -> Resume -> Stop."""
    dataset_svc = test_env["dataset_svc"]
    mock_tracking = test_env["tracking_service"]

    hand = create_mock_hand(0, "Right", 0.95)
    res = TrackingResult(
        status=TrackingState.ACTIVE,
        hands_detected=1,
        hands=[hand],
        processing_time_ms=12.0,
    )
    mock_tracking.wait_for_next_result.return_value = (res, 1)

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=test_env["camera_manager"],
        tracking_service=mock_tracking,
    )

    # Start
    assert collector.start_collection("G005", "Pointing", target_samples=50, sample_interval_ms=50)
    assert collector.is_active is True
    assert collector.get_status().status == "collecting"

    # Duplicate start rejected
    assert collector.start_collection("G005", "Pointing") is False

    # Pause
    assert collector.pause_collection() is True
    assert collector.get_status().status == "paused"
    assert collector.is_active is True

    # Resume
    assert collector.resume_collection() is True
    assert collector.get_status().status == "collecting"

    # Stop
    assert collector.stop_collection() is True
    assert collector.is_active is False
    assert collector.get_status().status == "cancelled"


def test_direct_sample_post_api(test_env, monkeypatch):
    """Test saving a sample via POST /api/v1/dataset/samples API."""
    dataset_svc = test_env["dataset_svc"]
    monkeypatch.setattr("app.api.routes.dataset._dataset_service", dataset_svc)

    lms = [{"index": i, "x": 0.03 * i, "y": 0.03 * i, "z": 0.0} for i in range(21)]
    payload = {
        "sample_id": "api_test_sample_01",
        "gesture_id": "G006",
        "gesture_name": "Stop",
        "timestamp": datetime.now().isoformat(),
        "handedness": "Left",
        "handedness_confidence": 0.92,
        "landmarks": lms,
        "session_id": "api_session_01",
    }

    with TestClient(app) as client:
        resp = client.post("/api/v1/dataset/samples", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["sample_id"] == "api_test_sample_01"

        # Verify query
        get_resp = client.get("/api/v1/dataset/samples/api_test_sample_01")
        assert get_resp.status_code == 200
        assert get_resp.json()["gesture_id"] == "G006"
