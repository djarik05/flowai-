"""
Tests for tracking API endpoints.

All tests mock the camera and MediaPipe detector so they do not require a
real webcam, internet access, or the downloaded model file.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_tracking_dependencies():
    """Mock camera VideoCapture and MediaPipe detector for all tracking API tests.

    Ensures no real camera hardware is opened, deterministic blank frames are
    returned, and MediaPipe HandLandmarker does not require model file on disk.
    """
    mock_landmarker = MagicMock()
    mock_result = MagicMock()
    mock_result.hand_landmarks = []
    mock_result.handedness = []
    mock_landmarker.detect.return_value = mock_result

    with patch(
        "app.services.hand_tracking.HandTrackingService._get_model_path",
        return_value="MOCKED_MODEL_PATH.task",
    ), patch(
        "mediapipe.tasks.python.vision.HandLandmarker.create_from_options",
        return_value=mock_landmarker,
    ), patch(
        "app.services.camera_manager.cv2"
    ) as mock_cv2:
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (
            True,
            np.zeros((480, 640, 3), dtype=np.uint8),
        )
        mock_cap.get.side_effect = lambda prop: {
            3: 640,    # CAP_PROP_FRAME_WIDTH
            4: 480,    # CAP_PROP_FRAME_HEIGHT
            5: 30.0,   # CAP_PROP_FPS
            6: 1400,   # CAP_PROP_BACKEND
        }.get(prop, 0)
        mock_cap.release.return_value = None
        mock_cv2.VideoCapture.return_value = mock_cap
        mock_cv2.flip = lambda frame, code: frame
        mock_cv2.CAP_PROP_FRAME_WIDTH = 3
        mock_cv2.CAP_PROP_FRAME_HEIGHT = 4
        mock_cv2.CAP_PROP_FPS = 5
        mock_cv2.CAP_PROP_BACKEND = 6
        mock_cv2.CAP_DSHOW = 1400
        mock_cv2.CAP_ANY = 0
        mock_cv2.COLOR_BGR2RGB = 4
        mock_cv2.IMWRITE_JPEG_QUALITY = 1
        mock_cv2.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))

        yield {
            "landmarker": mock_landmarker,
            "cv2": mock_cv2,
        }


@pytest.fixture
def client() -> TestClient:
    """Create test client with lifespan support and automatic service cleanup."""
    with TestClient(app) as c:
        yield c
        # Stop tracking and camera at the end of each test
        try:
            c.post("/api/v1/tracking/stop")
        except Exception:
            pass
        try:
            c.post("/api/v1/camera/stop")
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Endpoint Tests
# ---------------------------------------------------------------------------

def test_tracking_status_endpoint(client: TestClient) -> None:
    """Test tracking status endpoint."""
    response = client.get("/api/v1/tracking/status")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "state" in data
    assert "camera_active" in data
    assert "detector_initialized" in data
    assert "last_tracking_time" in data
    assert "frames_processed" in data
    assert "avg_processing_time_ms" in data
    assert "last_error" in data

    # Check state is valid
    assert data["state"] in [
        "not_initialized", "initializing", "active",
        "paused", "error", "stopped"
    ]


def test_tracking_result_endpoint(client: TestClient) -> None:
    """Test tracking result endpoint."""
    response = client.get("/api/v1/tracking/result")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "frame_width" in data
    assert "frame_height" in data
    assert "hands_detected" in data
    assert "hands" in data
    assert "frame_timestamp" in data
    assert "processing_time_ms" in data
    assert "error" in data

    # Check state is valid
    assert data["status"] in [
        "not_initialized", "initializing", "active",
        "paused", "error", "stopped"
    ]

    # Hands should be an array
    assert isinstance(data["hands"], list)


def test_tracking_start_endpoint(client: TestClient) -> None:
    """Test tracking start endpoint with mocked camera and detector."""
    response = client.post("/api/v1/tracking/start", json={})

    assert response.status_code in [200, 409]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "message" in data


def test_tracking_stop_endpoint(client: TestClient) -> None:
    """Test tracking stop endpoint."""
    response = client.post("/api/v1/tracking/stop")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_tracking_config_fields(client: TestClient) -> None:
    """Test tracking config request validation."""
    # Valid config
    valid_config = {
        "max_hands": 2,
        "detection_confidence": 0.7,
        "tracking_confidence": 0.5,
        "model_complexity": 1,
    }
    response = client.post("/api/v1/tracking/start", json=valid_config)
    assert response.status_code in [200, 409]

    # Invalid max_hands
    invalid_config = {
        "max_hands": 5,  # Too high
    }
    response = client.post("/api/v1/tracking/start", json=invalid_config)
    assert response.status_code == 422

    # Invalid confidence
    invalid_config = {
        "detection_confidence": 1.5,  # Too high
    }
    response = client.post("/api/v1/tracking/start", json=invalid_config)
    assert response.status_code == 422

    # Invalid model complexity
    invalid_config = {
        "model_complexity": 3,  # Too high
    }
    response = client.post("/api/v1/tracking/start", json=invalid_config)
    assert response.status_code == 422


def test_tracking_result_structure(client: TestClient) -> None:
    """Test tracking result structure with hands."""
    response = client.get("/api/v1/tracking/result")

    assert response.status_code == 200
    data = response.json()

    # If hands detected, check structure
    for hand in data["hands"]:
        assert "hand_id" in hand
        assert "landmarks" in hand
        assert "handedness" in hand
        assert "handedness_confidence" in hand
        assert "bounding_box" in hand
        assert "timestamp" in hand

        # Check landmarks
        assert isinstance(hand["landmarks"], list)
        for landmark in hand["landmarks"]:
            assert "index" in landmark
            assert "x" in landmark
            assert "y" in landmark
            assert "z" in landmark
            assert "pixel_x" in landmark
            assert "pixel_y" in landmark

            # Check normalized coordinates are in range
            assert 0.0 <= landmark["x"] <= 1.0
            assert 0.0 <= landmark["y"] <= 1.0
            assert landmark["index"] >= 0
            assert landmark["index"] <= 20

            # Check pixel coordinates are non-negative
            assert landmark["pixel_x"] >= 0
            assert landmark["pixel_y"] >= 0

        # Check handedness
        assert hand["handedness"] in ["Left", "Right", "Unknown"]
        assert 0.0 <= hand["handedness_confidence"] <= 1.0

        # Check bounding box if present
        if hand["bounding_box"] is not None:
            bbox = hand["bounding_box"]
            assert "x" in bbox
            assert "y" in bbox
            assert "width" in bbox
            assert "height" in bbox
            assert bbox["width"] >= 0
            assert bbox["height"] >= 0


def test_tracking_stream_endpoint(client: TestClient) -> None:
    """Test tracking stream endpoint connects and returns multipart content-type."""
    response = client.get("/api/v1/tracking/stream?max_frames=1")
    assert response.status_code == 200
    assert "multipart/x-mixed-replace" in response.headers.get("content-type", "")
    assert len(response.content) > 0
