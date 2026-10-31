"""
Tests for Gestures API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.gesture_service import GestureService


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    """Create test client with isolated gesture registry."""
    test_registry = tmp_path / "test_gestures" / "gesture_registry.json"
    test_service = GestureService(registry_file=test_registry)

    # Monkeypatch singleton in gestures route
    monkeypatch.setattr("app.api.routes.gestures._gesture_service", test_service)

    with TestClient(app) as c:
        yield c


def test_list_gestures(client: TestClient) -> None:
    """Test listing default gestures."""
    response = client.get("/api/v1/gestures")
    assert response.status_code == 200
    data = response.json()
    assert "gestures" in data
    assert "total" in data
    assert data["total"] >= 7
    # Verify Open Palm exists
    ids = [g["id"] for g in data["gestures"]]
    assert "G001" in ids


def test_create_custom_gesture(client: TestClient) -> None:
    """Test creating a new custom gesture."""
    payload = {
        "id": "G099",
        "name": "Spock Vulcan Salute",
        "description": "Fingers parted in V shape between middle and ring fingers",
        "type": "static",
        "action": "custom_shortcut",
        "enabled": True,
        "confidence_threshold": 0.85,
        "icon": "Sparkles",
    }
    response = client.post("/api/v1/gestures", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == "G099"
    assert created["name"] == "Spock Vulcan Salute"
    assert created["sample_count"] == 0

    # Verify duplicate ID returns 409
    dup_res = client.post("/api/v1/gestures", json=payload)
    assert dup_res.status_code == 409


def test_create_gesture_auto_id(client: TestClient) -> None:
    """Test creating a gesture without providing an ID (auto-generated G###)."""
    payload = {
        "name": "Auto ID Gesture",
        "description": "Auto ID generated",
    }
    response = client.post("/api/v1/gestures", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"].startswith("G")
    assert created["name"] == "Auto ID Gesture"


def test_get_gesture_by_id(client: TestClient) -> None:
    """Test getting a specific gesture."""
    response = client.get("/api/v1/gestures/G001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "G001"
    assert data["name"] == "Open Palm"

    # Not found
    not_found = client.get("/api/v1/gestures/NON_EXISTENT")
    assert not_found.status_code == 404


def test_update_gesture(client: TestClient) -> None:
    """Test updating gesture attributes."""
    update_payload = {
        "name": "Open Palm Renamed",
        "confidence_threshold": 0.9,
    }
    response = client.put("/api/v1/gestures/G001", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Open Palm Renamed"
    assert updated["confidence_threshold"] == 0.9


def test_delete_gesture(client: TestClient) -> None:
    """Test deleting a gesture."""
    # Create temporary gesture
    client.post("/api/v1/gestures", json={"id": "G_TEMP", "name": "Temporary"})
    
    del_res = client.delete("/api/v1/gestures/G_TEMP")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify it is gone
    check_res = client.get("/api/v1/gestures/G_TEMP")
    assert check_res.status_code == 404
