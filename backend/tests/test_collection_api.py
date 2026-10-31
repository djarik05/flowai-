"""
Tests for Live Collection API endpoints.
"""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_collector import DatasetCollector
from app.services.dataset_service import DatasetService
from app.services.gesture_service import GestureService


@pytest.fixture
def mock_collector(tmp_path, monkeypatch):
    """Create a collector with mocked tracking service and temporary dataset."""
    dataset_svc = DatasetService(dataset_dir=tmp_path / "test_collection_data")
    gesture_svc = GestureService(registry_file=tmp_path / "test_gestures.json")

    mock_camera = MagicMock()
    mock_camera.is_healthy.return_value = True

    mock_tracking = MagicMock()
    mock_tracking.is_active = True
    mock_tracking.start.return_value = True
    mock_tracking.wait_for_result.return_value = None

    collector = DatasetCollector(
        dataset_service=dataset_svc,
        camera_manager=mock_camera,
        tracking_service=mock_tracking,
    )

    monkeypatch.setattr("app.api.routes.collection._collector", collector)
    monkeypatch.setattr("app.api.routes.dataset._dataset_service", dataset_svc)
    monkeypatch.setattr("app.api.routes.gestures._gesture_service", gesture_svc)

    return collector


@pytest.fixture
def client(mock_collector) -> TestClient:
    """Create test client with mocked collector."""
    with TestClient(app) as c:
        yield c


def test_collection_status_idle(client: TestClient) -> None:
    """Test initial collection status."""
    res = client.get("/api/v1/collection/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "idle"
    assert data["collected_samples"] == 0


def test_collection_start_invalid_gesture(client: TestClient) -> None:
    """Test start collection with non-existent gesture returns 404."""
    payload = {
        "gesture_id": "NON_EXISTENT",
        "target_samples": 20,
    }
    res = client.post("/api/v1/collection/start", json=payload)
    assert res.status_code == 404


def test_collection_lifecycle(client: TestClient, mock_collector) -> None:
    """Test start, pause, resume, stop collection endpoints."""
    # 1. Start collection
    start_payload = {
        "gesture_id": "G001",
        "target_samples": 10,
        "sample_interval_ms": 100,
    }
    start_res = client.post("/api/v1/collection/start", json=start_payload)
    assert start_res.status_code == 200
    status_data = start_res.json()
    assert status_data["status"] == "collecting"
    assert status_data["target_samples"] == 10

    # 2. Duplicate start returns 409
    dup_res = client.post("/api/v1/collection/start", json=start_payload)
    assert dup_res.status_code == 409

    # 3. Pause collection
    pause_res = client.post("/api/v1/collection/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # 4. Resume collection
    resume_res = client.post("/api/v1/collection/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "collecting"

    # 5. Stop collection
    stop_res = client.post("/api/v1/collection/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "cancelled"
