"""
Tests for hand tracking service data structures and functionality.

Includes tests for:
- Data structures and serialisation
- Model path resolution (default, custom, missing, empty)
- Detector initialization (success, failure, missing model, no repeated init)
- Resource cleanup on stop
"""

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.core.config import Settings
from app.services.camera_manager import CameraManager
from app.services.hand_tracking import (
    DetectedHand,
    HandTrackingService,
    Landmark,
    TrackingResult,
    TrackingState,
)


# ============================================================================
# Data-structure / serialisation tests (no mocking needed)
# ============================================================================


def test_tracking_result_serialization():
    """Test tracking result data structure."""
    landmarks = [
        Landmark(index=0, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240),
        Landmark(index=8, x=0.5, y=0.3, z=-0.1, pixel_x=320, pixel_y=144),
    ]

    hand = DetectedHand(
        hand_id=0,
        landmarks=landmarks,
        handedness="Right",
        handedness_confidence=0.95,
        bounding_box={"x": 300, "y": 100, "width": 100, "height": 200},
    )

    result = TrackingResult(
        status=TrackingState.ACTIVE,
        frame_width=640,
        frame_height=480,
        hands_detected=1,
        hands=[hand],
        processing_time_ms=15.5,
    )

    # Verify structure
    assert result.status == TrackingState.ACTIVE
    assert result.frame_width == 640
    assert result.hands_detected == 1
    assert len(result.hands) == 1
    assert result.hands[0].handedness == "Right"
    assert result.hands[0].landmarks[0].pixel_x == 320
    assert result.hands[0].bounding_box["width"] == 100


def test_landmark_validation():
    """Test landmark coordinate validation."""
    # Valid landmark
    lm = Landmark(index=0, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240)
    assert lm.index == 0
    assert lm.x == 0.5
    assert lm.pixel_x == 320

    # Test boundary values
    lm_min = Landmark(index=0, x=0.0, y=0.0, z=-1.0, pixel_x=0, pixel_y=0)
    assert lm_min.x == 0.0
    assert lm_min.pixel_x == 0

    lm_max = Landmark(index=20, x=1.0, y=1.0, z=1.0, pixel_x=640, pixel_y=480)
    assert lm_max.x == 1.0
    assert lm_max.pixel_x == 640


def test_detected_hand_structure():
    """Test detected hand data structure."""
    landmarks = [
        Landmark(index=i, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240)
        for i in range(21)
    ]

    hand = DetectedHand(
        hand_id=0,
        landmarks=landmarks,
        handedness="Left",
        handedness_confidence=0.9,
        bounding_box={"x": 100, "y": 100, "width": 200, "height": 200},
    )

    assert hand.hand_id == 0
    assert hand.handedness == "Left"
    assert hand.handedness_confidence == 0.9
    assert len(hand.landmarks) == 21
    assert hand.bounding_box is not None
    assert hand.bounding_box["width"] == 200


def test_tracking_result_states():
    """Test all tracking states are valid."""
    for state in TrackingState:
        result = TrackingResult(
            status=state,
            frame_width=640,
            frame_height=480,
        )
        assert result.status == state


def test_tracking_result_with_error():
    """Test tracking result with error."""
    result = TrackingResult(
        status=TrackingState.ERROR,
        frame_width=640,
        frame_height=480,
        error="Camera disconnected",
    )

    assert result.status == TrackingState.ERROR
    assert result.error == "Camera disconnected"
    assert result.hands_detected == 0


def test_hand_tracking_service_creation():
    """Test HandTrackingService can be instantiated."""
    cm = CameraManager()
    hts = HandTrackingService(cm)

    assert hts is not None
    assert hts.status == TrackingState.NOT_INITIALIZED
    assert not hts.is_initialized
    assert not hts.is_active


def test_tracking_status_enum_values():
    """Test all tracking state enum values."""
    expected_states = {
        "not_initialized",
        "initializing",
        "active",
        "paused",
        "error",
        "stopped",
    }
    actual_states = {state.value for state in TrackingState}
    assert actual_states == expected_states


def test_landmark_index_range():
    """Test landmark index is in valid range (0-20)."""
    for i in range(21):
        lm = Landmark(index=i, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240)
        assert lm.index == i

    # Test boundary
    lm = Landmark(index=0, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240)
    assert lm.index == 0

    lm = Landmark(index=20, x=0.5, y=0.5, z=0.0, pixel_x=320, pixel_y=240)
    assert lm.index == 20


def test_bounding_box_structure():
    """Test bounding box dictionary structure."""
    hand = DetectedHand(
        hand_id=0,
        landmarks=[],
        handedness="Right",
        handedness_confidence=0.9,
        bounding_box={"x": 100, "y": 100, "width": 200, "height": 250},
    )

    assert hand.bounding_box is not None
    assert "x" in hand.bounding_box
    assert "y" in hand.bounding_box
    assert "width" in hand.bounding_box
    assert "height" in hand.bounding_box
    assert hand.bounding_box["width"] > 0
    assert hand.bounding_box["height"] > 0


def test_handedness_confidence_range():
    """Test handedness confidence is in valid range."""
    for conf in [0.0, 0.5, 0.99, 1.0]:
        hand = DetectedHand(
            hand_id=0,
            landmarks=[],
            handedness="Right",
            handedness_confidence=conf,
        )
        assert hand.handedness_confidence == conf


def test_tracking_result_timestamps():
    """Test tracking result has timestamp."""
    result = TrackingResult(
        status=TrackingState.ACTIVE,
        frame_width=640,
        frame_height=480,
    )

    assert result.frame_timestamp is not None
    assert isinstance(result.frame_timestamp, datetime)


# ============================================================================
# Model path resolution tests
# ============================================================================


def test_model_exists_and_path_resolves_correctly(tmp_path):
    """Test that existing model path resolves correctly to an absolute path."""
    model_file = tmp_path / "hand_landmarker.task"
    model_file.write_bytes(b"\x00" * 1024)

    service = HandTrackingService(model_path=model_file)
    resolved = service._get_model_path()
    assert resolved == str(model_file.resolve())
    assert Path(resolved).is_file()


def test_model_missing_raises_filenotfound():
    """Test that a missing model file raises FileNotFoundError with helpful message."""
    missing_path = Path("C:/missing_models/hand_landmarker.task")
    service = HandTrackingService(model_path=missing_path)

    with pytest.raises(FileNotFoundError) as exc_info:
        service._get_model_path()

    assert "Hand landmarker model not found" in str(exc_info.value)
    assert "Official download URL" in str(exc_info.value)


def test_model_empty_file_raises_filenotfound(tmp_path):
    """Test that a 0-byte model file is rejected as unusable."""
    empty_file = tmp_path / "empty_landmarker.task"
    empty_file.write_bytes(b"")

    service = HandTrackingService(model_path=empty_file)
    with pytest.raises(FileNotFoundError, match="empty"):
        service._get_model_path()


def test_custom_model_path_from_environment(tmp_path):
    """Test custom model path configured via HAND_LANDMARKER_MODEL_PATH environment variable."""
    custom_model = tmp_path / "custom_hand_landmarker.task"
    custom_model.write_bytes(b"\x00" * 2048)

    env_backup = dict(os.environ)
    os.environ["HAND_LANDMARKER_MODEL_PATH"] = str(custom_model)
    try:
        settings = Settings()
        assert settings.resolved_model_path == custom_model.resolve()

        # Service using these settings should resolve the custom path
        with patch("app.services.hand_tracking.settings", settings):
            service = HandTrackingService()
            resolved = service._get_model_path()
            assert resolved == str(custom_model.resolve())
    finally:
        os.environ.clear()
        os.environ.update(env_backup)


def test_relative_model_path_resolves_from_backend_dir():
    """Test that relative paths resolve relative to backend_dir."""
    settings = Settings(hand_landmarker_model_path="models/hand_landmarker.task")
    assert settings.resolved_model_path.is_absolute()
    assert "models" in str(settings.resolved_model_path)


# ============================================================================
# Detector initialization tests (mocked MediaPipe)
# ============================================================================


def test_successful_initialization_with_mocked_detector(tmp_path):
    """Test successful initialization with a mocked MediaPipe detector."""
    model_file = tmp_path / "hand_landmarker.task"
    model_file.write_bytes(b"\x00" * 1024)

    mock_detector = MagicMock()

    with patch("mediapipe.tasks.python.vision.HandLandmarker.create_from_options", return_value=mock_detector):
        service = HandTrackingService(model_path=model_file)
        success = service.initialize()

        assert success is True
        assert service.is_initialized is True
        assert service.status == TrackingState.ACTIVE
        assert service._last_error is None


def test_detector_initialization_failure_model_missing():
    """Test initialization fails cleanly when the model file is missing."""
    missing_path = Path("C:/does_not_exist/model.task")
    service = HandTrackingService(model_path=missing_path)

    success = service.initialize()

    assert success is False
    assert service.is_initialized is False
    assert service.status == TrackingState.ERROR
    assert service._last_error is not None
    assert "not found" in service._last_error


def test_detector_initialization_failure_mediapipe_error(tmp_path):
    """Test initialization fails cleanly when MediaPipe creation raises an error."""
    model_file = tmp_path / "corrupt_model.task"
    model_file.write_bytes(b"\x00" * 1024)

    with patch(
        "mediapipe.tasks.python.vision.HandLandmarker.create_from_options",
        side_effect=RuntimeError("Corrupt TFLite model format"),
    ):
        service = HandTrackingService(model_path=model_file)
        success = service.initialize()

        assert success is False
        assert service.is_initialized is False
        assert service.status == TrackingState.ERROR
        assert "Corrupt TFLite model format" in service._last_error


def test_no_repeated_model_initialization(tmp_path):
    """Test that calling initialize() multiple times does not recreate the detector."""
    model_file = tmp_path / "hand_landmarker.task"
    model_file.write_bytes(b"\x00" * 1024)

    mock_detector = MagicMock()
    create_mock = MagicMock(return_value=mock_detector)

    with patch("mediapipe.tasks.python.vision.HandLandmarker.create_from_options", create_mock):
        service = HandTrackingService(model_path=model_file)

        # First call
        success1 = service.initialize()
        assert success1 is True
        assert create_mock.call_count == 1

        # Second call should be a no-op
        success2 = service.initialize()
        assert success2 is True
        assert create_mock.call_count == 1  # Still 1, NOT called again


def test_detector_cleanup_on_stop(tmp_path):
    """Test that stop() cleans up detector resources and resets tracking state."""
    model_file = tmp_path / "hand_landmarker.task"
    model_file.write_bytes(b"\x00" * 1024)

    mock_detector = MagicMock()

    with patch("mediapipe.tasks.python.vision.HandLandmarker.create_from_options", return_value=mock_detector):
        service = HandTrackingService(model_path=model_file)
        service.initialize()
        assert service.is_initialized is True

        success = service.stop()

        assert success is True
        assert service.is_initialized is False
        assert service.status == TrackingState.STOPPED
        mock_detector.close.assert_called_once()
