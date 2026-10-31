"""
Tests for application status endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.status import StatusResponse, BackendState, ComponentState, ModelState


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create test client with lifespan support."""
    with TestClient(app) as c:
        yield c


def test_status_endpoint(client: TestClient) -> None:
    """Test status endpoint returns 200 and correct response."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    status = StatusResponse(**data)
    assert status.application == "GestureFlow AI"
    assert status.version == "1.0.0"
    assert status.environment == "development"
    assert status.backend_state == BackendState.READY
    assert status.current_phase == 1


def test_status_component_states_phase1(client: TestClient) -> None:
    """Test that component states correctly reflect Phase 1 (not implemented)."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()

    # Camera not initialized in Phase 1
    assert data["camera_state"] == ComponentState.NOT_INITIALIZED.value

    # Tracking not initialized in Phase 1
    assert data["tracking_state"] == ComponentState.NOT_INITIALIZED.value

    # Model not loaded in Phase 1
    assert data["model_state"] == ModelState.NOT_LOADED.value

    # Controller disabled in Phase 1
    assert data["controller_state"] == ComponentState.DISABLED.value


def test_status_response_schema(client: TestClient) -> None:
    """Test status response matches expected schema with all required fields."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()

    # Check all required fields present
    required_fields = [
        "application",
        "version",
        "environment",
        "backend_state",
        "current_phase",
        "camera_state",
        "tracking_state",
        "model_state",
        "controller_state",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check field types
    assert isinstance(data["application"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["environment"], str)
    assert isinstance(data["backend_state"], str)
    assert isinstance(data["current_phase"], int)
    assert isinstance(data["camera_state"], str)
    assert isinstance(data["tracking_state"], str)
    assert isinstance(data["model_state"], str)
    assert isinstance(data["controller_state"], str)


def test_status_phase_identification(client: TestClient) -> None:
    """Test that current_phase correctly identifies Phase 1."""
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    data = response.json()

    assert data["current_phase"] == 1
    assert isinstance(data["current_phase"], int)
    assert data["current_phase"] >= 1