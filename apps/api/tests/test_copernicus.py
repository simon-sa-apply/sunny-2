"""Tests for Copernicus service."""

import pytest

from app.services.copernicus import CopernicusService, SolarRadiationData


@pytest.fixture
def copernicus() -> CopernicusService:
    """Create Copernicus service instance."""
    return CopernicusService()


@pytest.mark.asyncio
async def test_fetch_mock_data(copernicus: CopernicusService) -> None:
    """Test fetching mock solar radiation data."""
    # Santiago, Chile
    data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    
    assert isinstance(data, SolarRadiationData)
    assert data.latitude == -33.45
    assert data.longitude == -70.65
    assert data.year == 2023
    assert len(data.ghi) > 0
    assert len(data.dni) > 0
    assert data.annual_ghi_kwh_m2 > 0


@pytest.mark.asyncio
async def test_monthly_ghi(copernicus: CopernicusService) -> None:
    """Test monthly GHI calculation."""
    data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    
    monthly = data.monthly_ghi
    assert len(monthly) == 12
    assert "Jan" in monthly
    assert "Dec" in monthly
    assert all(v >= 0 for v in monthly.values())


def test_coordinate_validation(copernicus: CopernicusService) -> None:
    """Test coordinate validation."""
    # Valid coordinates
    copernicus._validate_coordinates(45.0, 90.0)
    
    # Invalid latitude
    with pytest.raises(ValueError, match="out of range"):
        copernicus._validate_coordinates(100.0, 0.0)
    
    # High latitude warning (outside CAMS coverage)
    with pytest.raises(ValueError, match="outside CAMS coverage"):
        copernicus._validate_coordinates(70.0, 0.0)


def test_request_params(copernicus: CopernicusService) -> None:
    """Test request parameter building."""
    params = copernicus._build_request_params(-33.45, -70.65, 2023)
    
    assert params["sky_type"] == "observed_cloud"
    assert params["location"]["latitude"] == -33.45
    assert params["location"]["longitude"] == -70.65
    assert params["date"] == ["2023-01-01/2023-12-31"]
    assert params["time_step"] == "1hour"

