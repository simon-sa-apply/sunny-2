"""Solar analysis and cached location models."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Note: GeoAlchemy2 import is conditional to allow running without PostGIS
try:
    from geoalchemy2 import Geometry

    HAS_POSTGIS = True
except ImportError:
    HAS_POSTGIS = False
    Geometry = None  # type: ignore


class CachedLocation(Base):
    """
    Cached solar data for a geographic location.
    
    Stores the interpolation model for quick retrieval of solar calculations
    at any tilt/orientation combination without re-calling Copernicus API.
    """

    __tablename__ = "cached_locations"

    # Geographic location - using PostGIS POINT geometry
    # If PostGIS not available, falls back to lat/lon columns
    if HAS_POSTGIS:
        geom: Mapped[Any] = mapped_column(
            Geometry("POINT", srid=4326),
            nullable=True,
            index=True,
        )
    
    # Fallback lat/lon for non-PostGIS setups
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)

    # Pre-computed interpolation model for this location
    # Structure: {tilts: [], orientations: [], values: [][][], lat, lon, optimal_annual_kwh}
    interpolation_model: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Data quality tier
    data_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="standard",
    )  # 'engineering' | 'standard'

    # Source metadata
    source_dataset: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="CAMS",
    )  # 'ERA5-Land' | 'CAMS'

    # Country detected from coordinates
    country_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # Cache validity period (in days)
    cache_ttl_days: Mapped[int] = mapped_column(default=30)

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_cached_locations_lat_lon", "latitude", "longitude"),
        Index("ix_cached_locations_data_tier", "data_tier"),
    )

    def is_expired(self) -> bool:
        """Check if the cached data has expired."""
        from datetime import timedelta

        expiry = self.created_at + timedelta(days=self.cache_ttl_days)
        return datetime.now(self.created_at.tzinfo) > expiry


class SolarAnalysis(Base):
    """
    Individual solar analysis request/result.
    
    Stores the user's input parameters and the calculated results
    along with AI-generated insights.
    """

    __tablename__ = "solar_analyses"

    # Request parameters
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    tilt: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    orientation: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    # Calculated results
    annual_generation_kwh: Mapped[float] = mapped_column(Float, nullable=True)
    monthly_breakdown: Mapped[Optional[dict[str, float]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    peak_month: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    worst_month: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Data quality
    data_tier: Mapped[str] = mapped_column(String(20), default="standard")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8)

    # AI-generated insights
    ai_insights: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Country and regulatory info
    country_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    applied_plugin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Request tracking
    request_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )  # 'pending' | 'processing' | 'complete' | 'error'

    # API key that made the request (for tracking)
    api_key_id: Mapped[Optional[int]] = mapped_column(nullable=True)

    # Error information if status is 'error'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

