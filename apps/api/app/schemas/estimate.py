"""Schemas for solar estimation API."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class EstimateRequest(BaseModel):
    """Request body for solar estimation."""

    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    area_m2: float = Field(..., gt=0, le=10000, description="Panel area in m²")
    tilt: Optional[float] = Field(
        default=None,
        ge=0,
        le=90,
        description="Panel tilt in degrees (optional, uses optimal if not provided)",
    )
    orientation: Optional[str] = Field(
        default=None,
        pattern="^(N|S|E|W|NE|NW|SE|SW|auto)$",
        description="Cardinal orientation or 'auto' for optimal",
    )
    panel_efficiency: Optional[float] = Field(
        default=0.22,
        ge=0.10,
        le=0.30,
        description="Panel efficiency (0.18-0.25 for modern panels)",
    )
    electricity_price: Optional[float] = Field(
        default=None,
        gt=0,
        description="Local electricity price per kWh (for savings calculation)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "lat": -33.45,
                "lon": -70.65,
                "area_m2": 15.0,
                "tilt": 20.0,
                "orientation": "N",
            }
        }
    }


class LocationInfo(BaseModel):
    """Location information in response."""

    lat: float
    lon: float
    country_code: Optional[str] = None
    data_tier: str


class MonthlyBreakdown(BaseModel):
    """Monthly generation breakdown."""

    Jan: float
    Feb: float
    Mar: float
    Apr: float
    May: float
    Jun: float
    Jul: float
    Aug: float
    Sep: float
    Oct: float
    Nov: float
    Dec: float


class OptimizationInfo(BaseModel):
    """Optimization recommendations."""

    current_tilt: float
    current_orientation: float
    optimal_tilt: float
    optimal_orientation: float
    efficiency_vs_optimal: float
    optimal_annual_kwh: float


class SavingsInfo(BaseModel):
    """Economic savings information."""

    annual_savings: float
    monthly_average: float
    currency: str
    currency_symbol: str
    price_per_kwh: float
    co2_savings_kg: float
    advisory: Optional[str] = None


class EstimateResponse(BaseModel):
    """Response for solar estimation."""

    # Core results
    annual_generation_kwh: float
    monthly_breakdown: dict[str, float]
    peak_month: dict[str, Any]
    worst_month: dict[str, Any]

    # Location and data quality
    location: LocationInfo
    data_tier: str
    confidence_score: float

    # Optimization info
    optimization: OptimizationInfo

    # Economic calculations
    savings: Optional[SavingsInfo] = None

    # Applied regulatory plugin
    applied_plugin: Optional[str] = None

    # AI insights (null for now, filled by Gemini later)
    ai_insights: Optional[dict[str, Any]] = None

    # Request metadata
    request_id: str
    calculation_method: str = "Pvlib Simplified"

    model_config = {
        "json_schema_extra": {
            "example": {
                "annual_generation_kwh": 4250.5,
                "monthly_breakdown": {
                    "Jan": 450.2,
                    "Feb": 420.1,
                    "Mar": 380.5,
                    "Apr": 320.8,
                    "May": 280.3,
                    "Jun": 250.1,
                    "Jul": 260.5,
                    "Aug": 300.2,
                    "Sep": 350.8,
                    "Oct": 400.5,
                    "Nov": 420.3,
                    "Dec": 416.2,
                },
                "peak_month": {"month": "Jan", "kwh": 450.2},
                "worst_month": {"month": "Jun", "kwh": 250.1},
                "location": {
                    "lat": -33.45,
                    "lon": -70.65,
                    "country_code": "CL",
                    "data_tier": "engineering",
                },
                "data_tier": "engineering",
                "confidence_score": 0.92,
                "optimization": {
                    "current_tilt": 20.0,
                    "current_orientation": 0.0,
                    "optimal_tilt": 33.0,
                    "optimal_orientation": 0.0,
                    "efficiency_vs_optimal": 0.94,
                    "optimal_annual_kwh": 4520.0,
                },
                "applied_plugin": "Ley 21.118 - Net Billing",
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    }

