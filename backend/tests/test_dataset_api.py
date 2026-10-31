"""
Tests for Dataset API endpoints.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.dataset import DatasetSample, LandmarkCoord
from app.services.dataset_service import DatasetService


def make_sample(sample_id: str, gesture_id: str = "G001") -> DatasetSample:
    landmarks = [
        LandmarkCoord(index=i, x=0.5, y=0.5, z=0.0)
        for i in range(21)
    ]
    return DatasetSample(
        sample_id=sample_id,
        gesture_id=gesture_id,
        gesture_name="Open Palm",
        handedness="Right",
        handedness_confidence=0.99,
        landmarks=landmarks,
        session_id="session_test",
    )


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """Create test client with isolated dataset storage."""
    test_service = DatasetService(dataset_dir=tmp_path / "test_dataset_api")
    monkeypatch.setattr("app.api.routes.dataset._dataset_service", test_service)
    monkeypatch.setattr("app.api.routes.gestures._dataset_service", test_service)

    # Seed 2 samples
    test_service.save_sample(make_sample("sample_api_1", "G001"))
    test_service.save_sample(make_sample("sample_api_2", "G001"))

    with TestClient(app) as c:
        yield c


def test_get_dataset_stats_endpoint(client: TestClient) -> None:
    """Test /dataset/stats endpoint."""
    res = client.get("/api/v1/dataset/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_gestures" in data
    assert "total_samples" in data
    assert data["total_samples"] >= 2


def test_list_samples_endpoint(client: TestClient) -> None:
    """Test /dataset/samples endpoint."""
    res = client.get("/api/v1/dataset/samples")
    assert res.status_code == 200
    data = res.json()
    assert "samples" in data
    assert "total" in data
    assert data["total"] == 2
    assert len(data["samples"]) == 2


def test_get_sample_details_endpoint(client: TestClient) -> None:
    """Test /dataset/samples/{id} endpoint."""
    res = client.get("/api/v1/dataset/samples/sample_api_1")
    assert res.status_code == 200
    sample = res.json()
    assert sample["sample_id"] == "sample_api_1"
    assert len(sample["landmarks"]) == 21

    # 404 test
    not_found = client.get("/api/v1/dataset/samples/unknown_id")
    assert not_found.status_code == 404


def test_delete_sample_endpoint(client: TestClient) -> None:
    """Test deleting sample via API."""
    del_res = client.delete("/api/v1/dataset/samples/sample_api_1")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Confirm deleted
    check = client.get("/api/v1/dataset/samples/sample_api_1")
    assert check.status_code == 404


def test_validate_dataset_endpoint(client: TestClient) -> None:
    """Test /dataset/validate endpoint."""
    res = client.get("/api/v1/dataset/validate")
    assert res.status_code == 200
    report = res.json()
    assert "is_valid" in report
    assert "valid_samples" in report
    assert report["valid_samples"] >= 1


def test_export_csv_endpoint(client: TestClient) -> None:
    """Test /dataset/export/csv endpoint."""
    res = client.get("/api/v1/dataset/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert len(res.content) > 0


def test_export_json_endpoint(client: TestClient) -> None:
    """Test /dataset/export/json endpoint."""
    res = client.get("/api/v1/dataset/export/json")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    assert len(res.content) > 0
