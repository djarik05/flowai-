"""
Tests for health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.common import HealthResponse


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create test client with lifespan support."""
    with TestClient(app) as c:
        yield c


def test_health_check_endpoint(client: TestClient) -> None:
    """Test health check endpoint returns 200 and correct response."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Validate response structure
    health = HealthResponse(**data)
    assert health.status == "ok"
    assert health.application == "GestureFlow AI"
    assert health.version == "1.0.0"


def test_health_check_response_schema(client: TestClient) -> None:
    """Test health check response matches expected schema."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "status" in data
    assert "application" in data
    assert "version" in data

    # Check field types
    assert isinstance(data["status"], str)
    assert isinstance(data["application"], str)
    assert isinstance(data["version"], str)

    # Check values
    assert data["status"] == "ok"
    assert data["application"] == "GestureFlow AI"