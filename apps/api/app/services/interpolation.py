"""
Local Interpolation Model for real-time solar simulations.

Pre-computes a response matrix for all tilt/orientation combinations,
enabling <200ms interactive updates without external API calls.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.services.solar_calculator import SolarCalculator

logger = logging.getLogger(__name__)


@runtime_checkable
class SolarDataProtocol(Protocol):
    """Protocol for solar radiation data - allows both CAMS and PVGIS data."""
    latitude: float
    longitude: float
    year: int
    monthly_ghi: dict[str, float]
    data_tier: str


@dataclass
class InterpolationModel:
    """
    Pre-computed interpolation model for a geographic location.

    Contains a 3D response matrix: [tilts × orientations × months]
    that enables instant calculation for any tilt/orientation combination.
    """

    # Location
    latitude: float
    longitude: float

    # Pre-computed values
    tilts: list[float]  # 0-90° in 5° steps
    orientations: list[float]  # 0-360° in 15° steps
    monthly_values: list[list[list[float]]]  # [tilt_idx][orient_idx][month_idx]
    annual_values: list[list[float]]  # [tilt_idx][orient_idx] - annual totals

    # Optimal configuration
    optimal_tilt: float
    optimal_orientation: float
    optimal_annual_kwh: float

    # Metadata
    area_m2: float
    panel_efficiency: float
    data_tier: str
    year: int

    def interpolate(self, tilt: float, orientation: float) -> dict[str, Any]:
        """
        Interpolate generation values for given tilt/orientation.

        Uses bilinear interpolation for smooth transitions.

        Args:
            tilt: Panel tilt in degrees (0-90)
            orientation: Panel orientation in degrees (0-360)

        Returns:
            Dictionary with annual and monthly generation values
        """
        # Find surrounding indices
        tilt_idx, tilt_frac = self._find_index(tilt, self.tilts)
        orient_idx, orient_frac = self._find_index(orientation, self.orientations)

        # Get adjacent indices (with wraparound for orientation)
        t0, t1 = tilt_idx, min(tilt_idx + 1, len(self.tilts) - 1)
        o0, o1 = orient_idx, (orient_idx + 1) % len(self.orientations)

        # Bilinear interpolation for annual value
        v00 = self.annual_values[t0][o0]
        v01 = self.annual_values[t0][o1]
        v10 = self.annual_values[t1][o0]
        v11 = self.annual_values[t1][o1]

        annual = self._bilinear(v00, v01, v10, v11, tilt_frac, orient_frac)

        # Interpolate monthly values
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        monthly = {}
        for m_idx, month in enumerate(month_names):
            m00 = self.monthly_values[t0][o0][m_idx]
            m01 = self.monthly_values[t0][o1][m_idx]
            m10 = self.monthly_values[t1][o0][m_idx]
            m11 = self.monthly_values[t1][o1][m_idx]
            monthly[month] = self._bilinear(m00, m01, m10, m11, tilt_frac, orient_frac)

        # Find peak/worst months
        peak_month = max(monthly, key=monthly.get)  # type: ignore
        worst_month = min(monthly, key=monthly.get)  # type: ignore

        return {
            "annual_generation_kwh": round(annual, 1),
            "monthly_breakdown": {k: round(v, 1) for k, v in monthly.items()},
            "peak_month": {"month": peak_month, "kwh": round(monthly[peak_month], 1)},
            "worst_month": {"month": worst_month, "kwh": round(monthly[worst_month], 1)},
            "efficiency_vs_optimal": round(annual / self.optimal_annual_kwh, 3)
            if self.optimal_annual_kwh > 0
            else 1.0,
            "optimal_tilt": self.optimal_tilt,
            "optimal_orientation": self.optimal_orientation,
        }

    def _find_index(self, value: float, values: list[float]) -> tuple[int, float]:
        """Find index and fractional position for interpolation."""
        for i, v in enumerate(values):
            if value < v:
                if i == 0:
                    return 0, 0.0
                prev = values[i - 1]
                frac = (value - prev) / (v - prev)
                return i - 1, frac
        return len(values) - 1, 0.0

    def _bilinear(
        self,
        v00: float,
        v01: float,
        v10: float,
        v11: float,
        fx: float,
        fy: float,
    ) -> float:
        """Perform bilinear interpolation."""
        return (
            v00 * (1 - fx) * (1 - fy)
            + v01 * (1 - fx) * fy
            + v10 * fx * (1 - fy)
            + v11 * fx * fy
        )

    def to_json(self) -> str:
        """Serialize model to JSON for caching."""
        return json.dumps(
            {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "tilts": self.tilts,
                "orientations": self.orientations,
                "monthly_values": self.monthly_values,
                "annual_values": self.annual_values,
                "optimal_tilt": self.optimal_tilt,
                "optimal_orientation": self.optimal_orientation,
                "optimal_annual_kwh": self.optimal_annual_kwh,
                "area_m2": self.area_m2,
                "panel_efficiency": self.panel_efficiency,
                "data_tier": self.data_tier,
                "year": self.year,
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "InterpolationModel":
        """Deserialize model from JSON."""
        data = json.loads(json_str)
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return json.loads(self.to_json())


def generate_interpolation_model(
    solar_data: SolarDataProtocol,
    area_m2: float,
    panel_efficiency: float = 0.22,
    tilt_step: int = 5,
    orientation_step: int = 15,
) -> InterpolationModel:
    """
    Generate interpolation model from solar radiation data.

    Pre-computes generation values for all tilt/orientation combinations.

    Args:
        solar_data: Raw solar radiation data from Copernicus
        area_m2: Panel area in square meters
        panel_efficiency: Panel efficiency (0.18-0.25)
        tilt_step: Step size for tilt grid (degrees)
        orientation_step: Step size for orientation grid (degrees)

    Returns:
        InterpolationModel ready for caching and interpolation
    """
    calculator = SolarCalculator(panel_efficiency=panel_efficiency)

    # Define grid
    tilts = list(range(0, 91, tilt_step))  # 0, 5, 10, ... 90
    orientations = list(range(0, 360, orientation_step))  # 0, 15, 30, ... 345

    logger.info(
        f"Generating interpolation model: {len(tilts)}x{len(orientations)} grid"
    )

    # Pre-compute all values
    monthly_values: list[list[list[float]]] = []
    annual_values: list[list[float]] = []

    optimal_tilt = calculator.get_optimal_tilt(solar_data.latitude)
    optimal_orientation = calculator.get_optimal_orientation(solar_data.latitude)

    for tilt in tilts:
        tilt_monthly: list[list[float]] = []
        tilt_annual: list[float] = []

        for orient in orientations:
            # Calculate monthly generation
            monthly = calculator.calculate_monthly_generation(
                solar_data, area_m2, tilt, orient
            )

            # Store monthly values as list
            month_values = [
                monthly.get(m, 0)
                for m in [
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]
            ]
            tilt_monthly.append(month_values)
            tilt_annual.append(sum(month_values))

        monthly_values.append(tilt_monthly)
        annual_values.append(tilt_annual)

    # Find optimal values
    optimal_tilt_idx = tilts.index(
        min(tilts, key=lambda t: abs(t - optimal_tilt))
    )
    optimal_orient_idx = orientations.index(
        min(orientations, key=lambda o: abs(o - optimal_orientation))
    )
    optimal_annual_kwh = annual_values[optimal_tilt_idx][optimal_orient_idx]

    return InterpolationModel(
        latitude=solar_data.latitude,
        longitude=solar_data.longitude,
        tilts=tilts,
        orientations=orientations,
        monthly_values=monthly_values,
        annual_values=annual_values,
        optimal_tilt=optimal_tilt,
        optimal_orientation=optimal_orientation,
        optimal_annual_kwh=optimal_annual_kwh,
        area_m2=area_m2,
        panel_efficiency=panel_efficiency,
        data_tier=solar_data.data_tier,
        year=solar_data.year,
    )

