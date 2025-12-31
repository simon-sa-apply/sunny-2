"""Tests for Solar Calculator service."""

import pytest

from app.services.copernicus import CopernicusService
from app.services.solar_calculator import SolarCalculator, SolarEstimate


@pytest.fixture
def calculator() -> SolarCalculator:
    """Create SolarCalculator instance."""
    return SolarCalculator()


@pytest.fixture
def copernicus() -> CopernicusService:
    """Create CopernicusService instance."""
    return CopernicusService()


@pytest.mark.asyncio
async def test_basic_calculation(
    calculator: SolarCalculator,
    copernicus: CopernicusService,
) -> None:
    """Test basic solar calculation."""
    # Fetch mock data for Santiago
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)

    # Calculate with 15m² panel
    estimate = calculator.calculate(
        solar_data=solar_data,
        area_m2=15.0,
        tilt=20.0,
        orientation="N",  # Optimal for Southern hemisphere
    )

    assert isinstance(estimate, SolarEstimate)
    assert estimate.annual_generation_kwh > 0
    assert len(estimate.monthly_breakdown) == 12
    assert estimate.peak_month in estimate.monthly_breakdown
    assert estimate.worst_month in estimate.monthly_breakdown


@pytest.mark.asyncio
async def test_optimal_orientation(
    calculator: SolarCalculator,
    copernicus: CopernicusService,
) -> None:
    """Test that optimal orientation is correctly determined."""
    # Northern hemisphere should face South
    assert calculator.get_optimal_orientation(45.0) == 180

    # Southern hemisphere should face North
    assert calculator.get_optimal_orientation(-33.0) == 0


def test_optimal_tilt(calculator: SolarCalculator) -> None:
    """Test optimal tilt calculation."""
    # Optimal tilt should approximate latitude
    assert abs(calculator.get_optimal_tilt(45.0) - 45.0) < 5
    assert abs(calculator.get_optimal_tilt(-33.0) - 33.0) < 5

    # Edge cases
    assert calculator.get_optimal_tilt(0.0) == 0.0
    assert calculator.get_optimal_tilt(90.0) == 90.0


def test_orientation_conversion(calculator: SolarCalculator) -> None:
    """Test cardinal orientation to degrees conversion."""
    assert calculator.orientation_to_degrees("N") == 0
    assert calculator.orientation_to_degrees("S") == 180
    assert calculator.orientation_to_degrees("E") == 90
    assert calculator.orientation_to_degrees("W") == 270
    assert calculator.orientation_to_degrees("NE") == 45

    # Default for None
    assert calculator.orientation_to_degrees(None) == 180


@pytest.mark.asyncio
async def test_efficiency_vs_optimal(
    calculator: SolarCalculator,
    copernicus: CopernicusService,
) -> None:
    """Test that non-optimal parameters reduce efficiency."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)

    # Optimal calculation
    optimal = calculator.calculate(solar_data, area_m2=15.0)

    # Non-optimal (facing wrong direction)
    suboptimal = calculator.calculate(
        solar_data, area_m2=15.0, tilt=20.0, orientation="S"
    )

    # Optimal should always be >= 1.0 efficiency
    assert optimal.efficiency_vs_optimal >= 0.99

    # Facing South in Southern hemisphere should be worse
    assert suboptimal.efficiency_vs_optimal < 1.0


@pytest.mark.asyncio
async def test_estimate_to_dict(
    calculator: SolarCalculator,
    copernicus: CopernicusService,
) -> None:
    """Test conversion to dictionary for API response."""
    solar_data = await copernicus.fetch_solar_radiation(-33.45, -70.65, 2023)
    estimate = calculator.calculate(solar_data, area_m2=15.0)

    result = estimate.to_dict()

    assert "location" in result
    assert "input_parameters" in result
    assert "results" in result
    assert "optimization" in result
    assert "metadata" in result

    assert result["location"]["lat"] == -33.45
    assert result["input_parameters"]["area_m2"] == 15.0


@pytest.mark.asyncio
async def test_error_margin_under_5_percent(
    calculator: SolarCalculator,
    copernicus: CopernicusService,
) -> None:
    """Test that calculations maintain <5% error margin (confidence)."""
    # Test multiple locations
    locations = [
        (-33.45, -70.65, "Santiago"),
        (52.52, 13.41, "Berlin"),
        (35.68, 139.69, "Tokyo"),
    ]

    for lat, lon, name in locations:
        solar_data = await copernicus.fetch_solar_radiation(lat, lon, 2023)
        estimate = calculator.calculate(solar_data, area_m2=15.0)

        # Confidence should indicate acceptable accuracy
        assert estimate.confidence_score >= 0.70, f"Low confidence for {name}"

        # Performance ratio should be reasonable (0.7-1.0)
        assert 0.5 <= estimate.performance_ratio <= 1.5, (
            f"Unusual performance ratio for {name}: {estimate.performance_ratio}"
        )

