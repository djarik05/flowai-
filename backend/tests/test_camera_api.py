"""
Tests for camera API endpoints.

All camera operations use a mocked OpenCV VideoCapture device returning
deterministic frames to prevent real camera activation, dropped frames,
and hardware dependencies during testing.
"""

from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def mock_cv2():
    """Mock OpenCV VideoCapture for all camera API tests.

    Provides a healthy virtual camera device that yields deterministic frames
    and avoids activating actual webcam hardware.
    """
    with patch("app.services.camera_manager.cv2") as mock:
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
        mock.VideoCapture.return_value = mock_cap
        mock.flip = lambda frame, code: frame
        mock.CAP_PROP_FRAME_WIDTH = 3
        mock.CAP_PROP_FRAME_HEIGHT = 4
        mock.CAP_PROP_FPS = 5
        mock.CAP_PROP_BACKEND = 6
        mock.CAP_DSHOW = 1400
        mock.CAP_V4L2 = 200
        mock.CAP_MSMF = 1400
        mock.CAP_ANY = 0
        yield mock


@pytest.fixture
def client() -> TestClient:
    """Create test client with lifespan support and automatic cleanup."""
    with TestClient(app) as c:
        yield c
        # Ensure camera is stopped at end of each test to avoid orphan threads
        try:
            c.post("/api/v1/camera/stop")
        except Exception:
            pass


def test_camera_status_endpoint(client: TestClient) -> None:
    """Test camera status endpoint."""
    response = client.get("/api/v1/camera/status")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "state" in data
    assert "camera_index" in data
    assert "actual_width" in data
    assert "actual_height" in data
    assert "actual_fps" in data
    assert "backend" in data
    assert "is_capturing" in data
    assert "frames_captured" in data
    assert "frames_dropped" in data
    assert "last_error" in data
    assert "devices" in data

    # Check state is valid
    assert data["state"] in ["disconnected", "connecting", "connected", "capturing", "error"]


def test_camera_devices_endpoint(client: TestClient) -> None:
    """Test camera devices list endpoint."""
    response = client.get("/api/v1/camera/devices")

    assert response.status_code == 200
    data = response.json()

    assert "devices" in data
    assert isinstance(data["devices"], list)


def test_camera_start_endpoint(client: TestClient) -> None:
    """Test camera start endpoint."""
    # Camera might already be running from other tests, so accept 200 or 409
    response = client.post("/api/v1/camera/start", json={})

    assert response.status_code in [200, 409]
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "message" in data


def test_camera_stop_endpoint(client: TestClient) -> None:
    """Test camera stop endpoint."""
    response = client.post("/api/v1/camera/stop")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_camera_invalid_config(client: TestClient) -> None:
    """Test camera start with invalid config."""
    # Test with invalid camera index
    response = client.post("/api/v1/camera/start", json={"camera_index": -1})
    assert response.status_code in [400, 422]


def test_camera_config_fields(client: TestClient) -> None:
    """Test camera config request validation."""
    # Valid config
    valid_config = {
        "camera_index": 0,
        "width": 640,
        "height": 480,
        "fps": 30,
        "mirror": True,
    }
    response = client.post("/api/v1/camera/start", json=valid_config)
    assert response.status_code in [200, 409]

    # Invalid width
    invalid_config = {
        "camera_index": 0,
        "width": 100,  # Too small
    }
    response = client.post("/api/v1/camera/start", json=invalid_config)
    assert response.status_code == 422
