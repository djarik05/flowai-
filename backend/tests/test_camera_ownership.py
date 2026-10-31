"""
Unit tests for Camera Ownership Coordination and Lifecycle Safety.
Verifies Phase 5.5 Critical Stabilization acceptance criteria:
- Browser and backend ownership handoff
- Stop idempotency
- Safe executor shutdown
- Ownership API endpoints
"""

import threading
import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.camera_manager import CameraManager, CameraStatus, CameraState
from app.services.hand_tracking import HandTrackingService, TrackingState


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_camera_manager_ownership_lifecycle():
    manager = CameraManager()
    assert manager.get_owner() == "none"

    # Claim for browser
    assert manager.claim_ownership("browser") is True
    assert manager.get_owner() == "browser"
    assert manager.get_status().owner == "browser"

    # Claim for backend
    assert manager.claim_ownership("backend") is True
    assert manager.get_owner() == "backend"
    assert manager.get_status().owner == "backend"

    # Release ownership
    assert manager.release_ownership("backend") is True
    assert manager.get_owner() == "none"
    assert manager.get_status().owner == "none"


def test_camera_manager_browser_claim_stops_backend_capture():
    manager = CameraManager()
    manager._status.is_capturing = True
    manager._owner = "backend"

    with patch.object(manager, "stop") as mock_stop:
        assert manager.claim_ownership("browser") is True
        mock_stop.assert_called_once()
        assert manager.get_owner() == "browser"


def test_camera_ownership_api_endpoints(client):
    # Test GET /owner
    res = client.get("/api/v1/camera/owner")
    assert res.status_code == 200
    assert "owner" in res.json()

    # Test POST /claim for browser
    res = client.post("/api/v1/camera/claim", json={"owner": "browser"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["owner"] == "browser"

    # Verify status reflects ownership
    status_res = client.get("/api/v1/camera/status")
    assert status_res.status_code == 200
    assert status_res.json()["owner"] == "browser"

    # Test POST /release
    rel_res = client.post("/api/v1/camera/release", json={"owner": "browser"})
    assert rel_res.status_code == 200
    assert rel_res.json()["success"] is True
    assert rel_res.json()["owner"] == "none"


def test_hand_tracking_stop_idempotency_and_no_futures(tmp_path):
    model_file = tmp_path / "hand_landmarker.task"
    model_file.write_bytes(b"\x00" * 1024)

    mock_detector = MagicMock()
    with patch("mediapipe.tasks.python.vision.HandLandmarker.create_from_options", return_value=mock_detector):
        service = HandTrackingService(model_path=model_file)
        service.initialize()
        assert service.is_initialized is True

        # First stop
        assert service.stop() is True
        assert service.status == TrackingState.STOPPED
        mock_detector.close.assert_called_once()

        # Second stop (idempotent, must not crash or re-close)
        assert service.stop() is True
        assert service.status == TrackingState.STOPPED
        assert mock_detector.close.call_count == 1

        # Attempt to process frame after stop - must safely return STOPPED without submitting futures
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = service._process_frame(dummy_frame)
        assert result.status == TrackingState.STOPPED
        assert mock_detector.detect_for_video.call_count == 0
