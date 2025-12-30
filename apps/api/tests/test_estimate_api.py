"""Tests for estimate API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_estimate_endpoint(client: TestClient) -> None:
    """Test basic estimate endpoint."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
            "tilt": 20.0,
            "orientation": "N",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "annual_generation_kwh" in data
    assert "monthly_breakdown" in data
    assert "peak_month" in data
    assert "worst_month" in data
    assert "location" in data
    assert "confidence_score" in data
    assert "request_id" in data
    
    # Check values are reasonable
    assert data["annual_generation_kwh"] > 0
    assert len(data["monthly_breakdown"]) == 12
    assert 0 < data["confidence_score"] <= 1


def test_estimate_with_auto_orientation(client: TestClient) -> None:
    """Test estimate with automatic orientation."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
            "orientation": "auto",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should use optimal orientation
    assert data["optimization"]["efficiency_vs_optimal"] >= 0.99


def test_estimate_response_headers(client: TestClient) -> None:
    """Test that response includes expected headers."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
        },
    )
    
    assert response.status_code == 200
    assert "X-Data-Tier" in response.headers
    assert "X-Confidence-Score" in response.headers
    assert "X-Request-ID" in response.headers


def test_estimate_chile_plugin(client: TestClient) -> None:
    """Test that Chile plugin is applied for Chilean coordinates."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["location"]["country_code"] == "CL"
    assert "Ley 21.118" in data["applied_plugin"]
    assert data["savings"] is not None
    assert data["savings"]["currency"] == "USD"


def test_estimate_germany_plugin(client: TestClient) -> None:
    """Test that Germany plugin is applied for German coordinates."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": 52.52,
            "lon": 13.41,
            "area_m2": 15.0,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["location"]["country_code"] == "DE"
    assert "EEG" in data["applied_plugin"]
    assert data["savings"]["currency"] == "USD"


def test_estimate_validation_error(client: TestClient) -> None:
    """Test validation error for invalid coordinates."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": 100.0,  # Invalid latitude
            "lon": -70.65,
            "area_m2": 15.0,
        },
    )
    
    assert response.status_code == 422  # Validation error


def test_estimate_with_custom_price(client: TestClient) -> None:
    """Test estimate with custom electricity price."""
    response = client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
            "electricity_price": 200.0,  # Custom CLP price
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["savings"]["price_per_kwh"] == 200.0


def test_interpolate_endpoint(client: TestClient) -> None:
    """Test quick interpolation endpoint."""
    # First, create a model via estimate
    client.post(
        "/api/v1/estimate",
        json={
            "lat": -33.45,
            "lon": -70.65,
            "area_m2": 15.0,
        },
    )
    
    # Then test interpolation
    response = client.post(
        "/api/v1/interpolate",
        params={
            "lat": -33.45,
            "lon": -70.65,
            "tilt": 25.0,
            "orientation": 180.0,
            "area_m2": 15.0,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "annual_generation_kwh" in data
    assert "monthly_breakdown" in data

