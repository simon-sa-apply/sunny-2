"""Tests for health check endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint returns healthy status."""
    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "services" in data


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns API info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "sunny-2 API"
    assert "version" in data
    assert "docs" in data

