"""Tests for Interpolation model."""

import pytest
import time

from app.services.copernicus import CopernicusService
from app.services.interpolation import InterpolationModel, generate_interpolation_model


@pytest.fixture
def copernicus() -> CopernicusService:
    """Create CopernicusService instance."""
    return CopernicusService()


@pytest.mark.asyncio
async def test_generate_model(copernicus: CopernicusService) -> None:
    """Test generating interpolation model."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    
    model = generate_interpolation_model(
        solar_data=solar_data,
        area_m2=15.0,
        panel_efficiency=0.22,
    )
    
    assert isinstance(model, InterpolationModel)
    assert model.latitude == -33.45
    assert model.longitude == -70.65
    assert len(model.tilts) > 0
    assert len(model.orientations) > 0
    assert model.optimal_annual_kwh > 0


@pytest.mark.asyncio
async def test_interpolation_speed(copernicus: CopernicusService) -> None:
    """Test that interpolation is fast (<200ms)."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    model = generate_interpolation_model(solar_data, area_m2=15.0)
    
    # Time multiple interpolations
    start = time.time()
    for _ in range(100):
        model.interpolate(tilt=25.0, orientation=180.0)
    elapsed = time.time() - start
    
    # 100 interpolations should take < 100ms (1ms each)
    assert elapsed < 0.1, f"Interpolation too slow: {elapsed*1000/100:.2f}ms per call"


@pytest.mark.asyncio
async def test_interpolation_accuracy(copernicus: CopernicusService) -> None:
    """Test interpolation returns sensible values."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    model = generate_interpolation_model(solar_data, area_m2=15.0)
    
    result = model.interpolate(tilt=30.0, orientation=0.0)  # Facing North
    
    assert "annual_generation_kwh" in result
    assert "monthly_breakdown" in result
    assert "peak_month" in result
    assert "worst_month" in result
    assert "efficiency_vs_optimal" in result
    
    assert result["annual_generation_kwh"] > 0
    assert len(result["monthly_breakdown"]) == 12
    assert 0 < result["efficiency_vs_optimal"] <= 1.0


@pytest.mark.asyncio
async def test_optimal_vs_suboptimal(copernicus: CopernicusService) -> None:
    """Test that optimal orientation gives best results."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    model = generate_interpolation_model(solar_data, area_m2=15.0)
    
    # Optimal for Southern hemisphere: facing North (0°)
    optimal = model.interpolate(tilt=model.optimal_tilt, orientation=0)
    
    # Suboptimal: facing South (180°) in Southern hemisphere
    suboptimal = model.interpolate(tilt=30.0, orientation=180)
    
    assert optimal["annual_generation_kwh"] >= suboptimal["annual_generation_kwh"]


@pytest.mark.asyncio
async def test_json_serialization(copernicus: CopernicusService) -> None:
    """Test model can be serialized and deserialized."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    model = generate_interpolation_model(solar_data, area_m2=15.0)
    
    # Serialize
    json_str = model.to_json()
    assert len(json_str) > 0
    
    # Deserialize
    restored = InterpolationModel.from_json(json_str)
    
    assert restored.latitude == model.latitude
    assert restored.longitude == model.longitude
    assert restored.optimal_annual_kwh == model.optimal_annual_kwh
    
    # Verify interpolation works on restored model
    result = restored.interpolate(tilt=25.0, orientation=180.0)
    assert result["annual_generation_kwh"] > 0


@pytest.mark.asyncio
async def test_edge_cases(copernicus: CopernicusService) -> None:
    """Test edge case inputs."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    model = generate_interpolation_model(solar_data, area_m2=15.0)
    
    # Extreme tilt values
    flat = model.interpolate(tilt=0.0, orientation=180.0)
    vertical = model.interpolate(tilt=90.0, orientation=180.0)
    
    assert flat["annual_generation_kwh"] > 0
    assert vertical["annual_generation_kwh"] > 0
    
    # All orientations should work
    for orient in [0, 45, 90, 135, 180, 225, 270, 315]:
        result = model.interpolate(tilt=30.0, orientation=float(orient))
        assert result["annual_generation_kwh"] > 0

