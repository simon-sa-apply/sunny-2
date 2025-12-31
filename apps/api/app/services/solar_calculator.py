"""
Solar Generation Calculator using Pvlib.

Calculates solar energy potential based on location, panel parameters,
and irradiance data from Copernicus CDSE.

References:
- https://pvlib-python.readthedocs.io/
- IEC 61724 - Photovoltaic system performance monitoring
"""

import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np

logger = logging.getLogger(__name__)


@runtime_checkable
class SolarDataProtocol(Protocol):
    """Protocol for solar radiation data - allows both CAMS and PVGIS data."""
    latitude: float
    longitude: float
    year: int
    monthly_ghi: dict[str, float]
    data_tier: str


# Panel efficiency constants (TOPCon technology, 2024-2025)
DEFAULT_PANEL_EFFICIENCY = 0.22  # 22% - mid-range TOPCon
MIN_PANEL_EFFICIENCY = 0.18
MAX_PANEL_EFFICIENCY = 0.25

# System losses
INVERTER_EFFICIENCY = 0.97
WIRING_LOSSES = 0.02
SOILING_LOSSES = 0.02
TEMPERATURE_COEFFICIENT = -0.004  # %/°C for silicon panels


@dataclass
class SolarEstimate:
    """Solar generation estimate results."""

    # Location
    latitude: float
    longitude: float

    # Input parameters
    area_m2: float
    tilt: float
    orientation: float  # Degrees from North (0=N, 90=E, 180=S, 270=W)

    # Results
    annual_generation_kwh: float
    monthly_breakdown: dict[str, float]
    peak_month: str
    peak_month_kwh: float
    worst_month: str
    worst_month_kwh: float

    # Optimal values (for comparison)
    optimal_tilt: float
    optimal_orientation: float
    optimal_annual_kwh: float
    efficiency_vs_optimal: float

    # Metadata
    panel_efficiency: float
    data_tier: str
    confidence_score: float
    calculation_method: str = "Pvlib Simplified"

    # Additional analysis
    capacity_factor: float = 0.0
    performance_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "location": {"lat": self.latitude, "lon": self.longitude},
            "input_parameters": {
                "area_m2": self.area_m2,
                "tilt": self.tilt,
                "orientation": self.orientation,
            },
            "results": {
                "annual_generation_kwh": round(self.annual_generation_kwh, 1),
                "monthly_breakdown": {k: round(v, 1) for k, v in self.monthly_breakdown.items()},
                "peak_month": {"month": self.peak_month, "kwh": round(self.peak_month_kwh, 1)},
                "worst_month": {"month": self.worst_month, "kwh": round(self.worst_month_kwh, 1)},
            },
            "optimization": {
                "optimal_tilt": round(self.optimal_tilt, 1),
                "optimal_orientation": round(self.optimal_orientation, 1),
                "optimal_annual_kwh": round(self.optimal_annual_kwh, 1),
                "efficiency_vs_optimal": round(self.efficiency_vs_optimal * 100, 1),
            },
            "metadata": {
                "panel_efficiency": self.panel_efficiency,
                "data_tier": self.data_tier,
                "confidence_score": round(self.confidence_score, 2),
                "calculation_method": self.calculation_method,
            },
        }


class SolarCalculator:
    """
    Solar generation calculator.

    Calculates potential solar energy generation based on location,
    panel parameters, and irradiance data.
    """

    # Orientation mapping (cardinal to degrees from North)
    ORIENTATION_MAP = {
        "N": 0,
        "NE": 45,
        "E": 90,
        "SE": 135,
        "S": 180,
        "SW": 225,
        "W": 270,
        "NW": 315,
    }

    def __init__(
        self,
        panel_efficiency: float = DEFAULT_PANEL_EFFICIENCY,
    ) -> None:
        self.panel_efficiency = panel_efficiency

    def orientation_to_degrees(self, orientation: str | None) -> float:
        """Convert cardinal orientation to degrees."""
        if orientation is None:
            return 180  # Default to South (optimal for Northern hemisphere)
        return self.ORIENTATION_MAP.get(orientation.upper(), 180)

    def get_optimal_tilt(self, latitude: float) -> float:
        """
        Calculate optimal panel tilt for maximum annual generation.

        Rule of thumb: optimal tilt ≈ latitude for annual optimization.
        Adjusted slightly for specific hemisphere considerations.
        """
        # Optimal tilt is approximately equal to latitude
        optimal = abs(latitude)

        # Slight adjustment based on typical use patterns
        # Summer optimization: subtract 10-15 degrees
        # Winter optimization: add 10-15 degrees
        # Annual average: use latitude

        return min(max(optimal, 0), 90)

    def get_optimal_orientation(self, latitude: float) -> float:
        """
        Get optimal panel orientation for location.

        Returns:
            Orientation in degrees from North (0=N, 180=S)
        """
        # Northern hemisphere: face South (180°)
        # Southern hemisphere: face North (0°)
        return 180 if latitude > 0 else 0

    def calculate_tilt_factor(
        self,
        tilt: float,
        orientation: float,
        latitude: float,
    ) -> float:
        """
        Calculate efficiency factor based on tilt and orientation vs optimal.

        Uses simplified geometric model for panel efficiency.
        """
        optimal_tilt = self.get_optimal_tilt(latitude)
        optimal_orientation = self.get_optimal_orientation(latitude)

        # Tilt deviation penalty (max ~30% loss for 90° off optimal)
        tilt_diff = abs(tilt - optimal_tilt)
        tilt_factor = np.cos(np.radians(tilt_diff * 0.9))

        # Orientation deviation penalty
        orientation_diff = abs(orientation - optimal_orientation)
        if orientation_diff > 180:
            orientation_diff = 360 - orientation_diff
        orientation_factor = np.cos(np.radians(orientation_diff * 0.5))

        # Combined factor (multiplicative)
        return float(max(0.5, tilt_factor * orientation_factor))

    def calculate_monthly_generation(
        self,
        solar_data: SolarDataProtocol,
        area_m2: float,
        tilt: float,
        orientation: float,
    ) -> dict[str, float]:
        """
        Calculate monthly generation from radiation data.

        Args:
            solar_data: Solar radiation data from Copernicus
            area_m2: Panel area in square meters
            tilt: Panel tilt in degrees
            orientation: Panel orientation in degrees from North

        Returns:
            Dictionary of monthly generation in kWh
        """
        # Get monthly GHI
        monthly_ghi = solar_data.monthly_ghi

        # Calculate adjustment factor for tilt/orientation
        tilt_factor = self.calculate_tilt_factor(
            tilt, orientation, solar_data.latitude
        )

        # System efficiency factors
        system_efficiency = (
            self.panel_efficiency
            * INVERTER_EFFICIENCY
            * (1 - WIRING_LOSSES)
            * (1 - SOILING_LOSSES)
        )

        # Calculate generation for each month
        monthly_generation = {}
        for month, ghi_kwh_m2 in monthly_ghi.items():
            # Generation = GHI * Area * Tilt Factor * System Efficiency
            generation = ghi_kwh_m2 * area_m2 * tilt_factor * system_efficiency
            monthly_generation[month] = generation

        return monthly_generation

    def calculate(
        self,
        solar_data: SolarDataProtocol,
        area_m2: float,
        tilt: float | None = None,
        orientation: str | None = None,
    ) -> SolarEstimate:
        """
        Calculate solar generation potential.

        Args:
            solar_data: Solar radiation data from Copernicus
            area_m2: Panel area in square meters
            tilt: Panel tilt in degrees (optional, uses optimal if None)
            orientation: Cardinal direction (N/S/E/W/NE/etc) or None for optimal

        Returns:
            SolarEstimate with full calculation results
        """
        lat = solar_data.latitude
        lon = solar_data.longitude

        # Determine tilt and orientation
        optimal_tilt = self.get_optimal_tilt(lat)
        optimal_orientation = self.get_optimal_orientation(lat)

        actual_tilt = tilt if tilt is not None else optimal_tilt
        actual_orientation = (
            self.orientation_to_degrees(orientation)
            if orientation
            else optimal_orientation
        )

        # Calculate monthly generation for actual parameters
        monthly = self.calculate_monthly_generation(
            solar_data, area_m2, actual_tilt, actual_orientation
        )

        # Calculate optimal generation for comparison
        optimal_monthly = self.calculate_monthly_generation(
            solar_data, area_m2, optimal_tilt, optimal_orientation
        )
        optimal_annual = sum(optimal_monthly.values())

        # Find peak and worst months
        peak_month = max(monthly, key=monthly.get)  # type: ignore
        worst_month = min(monthly, key=monthly.get)  # type: ignore

        annual_kwh = sum(monthly.values())
        efficiency = annual_kwh / optimal_annual if optimal_annual > 0 else 0

        # Calculate performance metrics
        # Capacity factor: actual generation / theoretical max
        theoretical_max = area_m2 * self.panel_efficiency * 8760 * 0.25  # 25% avg sunlight
        capacity_factor = annual_kwh / theoretical_max if theoretical_max > 0 else 0

        # Performance ratio: actual / expected based on irradiance
        expected = solar_data.annual_ghi_kwh_m2 * area_m2 * self.panel_efficiency
        performance_ratio = annual_kwh / expected if expected > 0 else 0

        # Confidence score based on data tier and location
        confidence = 0.9 if solar_data.data_tier == "engineering" else 0.75
        if abs(lat) > 50:
            confidence *= 0.9  # Reduce confidence for high latitudes

        return SolarEstimate(
            latitude=lat,
            longitude=lon,
            area_m2=area_m2,
            tilt=actual_tilt,
            orientation=actual_orientation,
            annual_generation_kwh=annual_kwh,
            monthly_breakdown=monthly,
            peak_month=peak_month,
            peak_month_kwh=monthly[peak_month],
            worst_month=worst_month,
            worst_month_kwh=monthly[worst_month],
            optimal_tilt=optimal_tilt,
            optimal_orientation=optimal_orientation,
            optimal_annual_kwh=optimal_annual,
            efficiency_vs_optimal=efficiency,
            panel_efficiency=self.panel_efficiency,
            data_tier=solar_data.data_tier,
            confidence_score=confidence,
            capacity_factor=capacity_factor,
            performance_ratio=performance_ratio,
        )


# Singleton instance
solar_calculator = SolarCalculator()

