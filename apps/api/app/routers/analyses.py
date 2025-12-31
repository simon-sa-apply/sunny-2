"""
Analyses history endpoints.

Provides access to historical solar analyses for authenticated API users.
"""

import logging
from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.solar_analysis import SolarAnalysis
from app.repositories.api_keys_repository import api_keys_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analyses", tags=["Analyses History"])


# ============================================
# Response Models
# ============================================


class AnalysisSummary(BaseModel):
    """Summary of a solar analysis."""

    request_id: str
    latitude: float
    longitude: float
    area_m2: float
    tilt: float | None
    orientation: str | None
    annual_generation_kwh: float | None
    data_tier: str
    confidence_score: float
    status: str
    country_code: str | None
    created_at: str

    class Config:
        from_attributes = True


class AnalysisDetail(AnalysisSummary):
    """Full details of a solar analysis."""

    monthly_breakdown: dict[str, float] | None
    peak_month: str | None
    worst_month: str | None
    ai_insights: dict[str, Any] | None
    applied_plugin: str | None
    error_message: str | None
    updated_at: str


class PaginatedAnalysesResponse(BaseModel):
    """Paginated list of analyses."""

    total_count: int
    limit: int
    offset: int
    items: list[AnalysisSummary]


class AnalysesStatsResponse(BaseModel):
    """Statistics about analyses."""

    total_analyses: int
    successful_analyses: int
    failed_analyses: int
    pending_analyses: int
    avg_generation_kwh: float | None
    most_common_country: str | None
    analyses_last_24h: int
    analyses_last_7d: int


# ============================================
# Auth Helper
# ============================================


async def get_current_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> dict[str, Any]:
    """Validate API key and return key info."""
    is_valid, key_info = await api_keys_repository.validate(x_api_key)

    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key",
        )

    # Record usage
    await api_keys_repository.record_usage(x_api_key)

    return key_info


# ============================================
# Endpoints
# ============================================


@router.get("", response_model=PaginatedAnalysesResponse)
async def list_analyses(
    limit: int = Query(20, ge=1, le=100, description="Max items per page"),
    offset: int = Query(0, ge=0, description="Items to skip"),
    from_date: date | None = Query(None, description="Filter from date (YYYY-MM-DD)"),  # noqa: B008
    to_date: date | None = Query(None, description="Filter to date (YYYY-MM-DD)"),  # noqa: B008
    status: str | None = Query(  # noqa: B008
        None,
        description="Filter by status",
        pattern="^(pending|processing|complete|error)$",
    ),
    lat: float | None = Query(None, ge=-90, le=90, description="Center latitude for geo filter"),  # noqa: B008
    lon: float | None = Query(None, ge=-180, le=180, description="Center longitude for geo filter"),  # noqa: B008
    radius_km: float = Query(10, ge=1, le=100, description="Search radius in km"),
    db: AsyncSession = Depends(get_db),  # noqa: B008
    api_key: dict[str, Any] = Depends(get_current_api_key),  # noqa: B008
) -> PaginatedAnalysesResponse:
    """
    List analyses for the current API key.

    Supports pagination and filtering by:
    - Date range
    - Status
    - Geographic location (center + radius)

    Returns analyses ordered by creation date (newest first).
    """
    api_key_id = api_key.get("id")

    # Build base query
    conditions = [SolarAnalysis.api_key_id == api_key_id]

    if from_date:
        conditions.append(SolarAnalysis.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        conditions.append(SolarAnalysis.created_at <= datetime.combine(to_date, datetime.max.time()))
    if status:
        conditions.append(SolarAnalysis.status == status)

    # Geographic filter using bounding box approximation
    if lat is not None and lon is not None:
        # 1 degree ≈ 111 km at equator
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * abs(lat) / 90 + 0.001)  # Avoid div by zero

        conditions.append(
            and_(
                SolarAnalysis.latitude.between(lat - lat_offset, lat + lat_offset),
                SolarAnalysis.longitude.between(lon - lon_offset, lon + lon_offset),
            )
        )

    # Count total
    count_stmt = select(func.count(SolarAnalysis.id)).where(and_(*conditions))
    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar() or 0

    # Get paginated items
    items_stmt = (
        select(SolarAnalysis)
        .where(and_(*conditions))
        .order_by(SolarAnalysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    items_result = await db.execute(items_stmt)
    analyses = items_result.scalars().all()

    return PaginatedAnalysesResponse(
        total_count=total_count,
        limit=limit,
        offset=offset,
        items=[
            AnalysisSummary(
                request_id=a.request_id,
                latitude=a.latitude,
                longitude=a.longitude,
                area_m2=a.area_m2,
                tilt=a.tilt,
                orientation=a.orientation,
                annual_generation_kwh=a.annual_generation_kwh,
                data_tier=a.data_tier,
                confidence_score=a.confidence_score,
                status=a.status,
                country_code=a.country_code,
                created_at=a.created_at.isoformat() if a.created_at else "",
            )
            for a in analyses
        ],
    )


@router.get("/stats", response_model=AnalysesStatsResponse)
async def get_analyses_stats(
    db: AsyncSession = Depends(get_db),  # noqa: B008
    api_key: dict[str, Any] = Depends(get_current_api_key),  # noqa: B008
) -> AnalysesStatsResponse:
    """
    Get statistics about your analyses.

    Returns aggregate information including:
    - Total, successful, failed, pending counts
    - Average generation
    - Most common country
    - Recent activity
    """
    api_key_id = api_key.get("id")
    now = datetime.now(UTC)

    # Total count
    total_result = await db.execute(
        select(func.count(SolarAnalysis.id)).where(SolarAnalysis.api_key_id == api_key_id)
    )
    total = total_result.scalar() or 0

    # Status counts
    status_result = await db.execute(
        select(SolarAnalysis.status, func.count(SolarAnalysis.id))
        .where(SolarAnalysis.api_key_id == api_key_id)
        .group_by(SolarAnalysis.status)
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}

    # Average generation
    avg_result = await db.execute(
        select(func.avg(SolarAnalysis.annual_generation_kwh)).where(
            and_(
                SolarAnalysis.api_key_id == api_key_id,
                SolarAnalysis.status == "complete",
                SolarAnalysis.annual_generation_kwh.isnot(None),
            )
        )
    )
    avg_generation = avg_result.scalar()

    # Most common country
    country_result = await db.execute(
        select(SolarAnalysis.country_code, func.count(SolarAnalysis.id).label("cnt"))
        .where(
            and_(
                SolarAnalysis.api_key_id == api_key_id,
                SolarAnalysis.country_code.isnot(None),
            )
        )
        .group_by(SolarAnalysis.country_code)
        .order_by(func.count(SolarAnalysis.id).desc())
        .limit(1)
    )
    country_row = country_result.fetchone()
    most_common_country = country_row[0] if country_row else None

    # Last 24h
    last_24h_result = await db.execute(
        select(func.count(SolarAnalysis.id)).where(
            and_(
                SolarAnalysis.api_key_id == api_key_id,
                SolarAnalysis.created_at >= now - func.make_interval(hours=24),
            )
        )
    )
    last_24h = last_24h_result.scalar() or 0

    # Last 7d
    last_7d_result = await db.execute(
        select(func.count(SolarAnalysis.id)).where(
            and_(
                SolarAnalysis.api_key_id == api_key_id,
                SolarAnalysis.created_at >= now - func.make_interval(days=7),
            )
        )
    )
    last_7d = last_7d_result.scalar() or 0

    return AnalysesStatsResponse(
        total_analyses=total,
        successful_analyses=status_counts.get("complete", 0),
        failed_analyses=status_counts.get("error", 0),
        pending_analyses=status_counts.get("pending", 0) + status_counts.get("processing", 0),
        avg_generation_kwh=round(avg_generation, 2) if avg_generation else None,
        most_common_country=most_common_country,
        analyses_last_24h=last_24h,
        analyses_last_7d=last_7d,
    )


@router.get("/{request_id}", response_model=AnalysisDetail)
async def get_analysis(
    request_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
    api_key: dict[str, Any] = Depends(get_current_api_key),  # noqa: B008
) -> AnalysisDetail:
    """
    Get detailed information about a specific analysis.

    Returns full analysis data including:
    - Monthly breakdown
    - AI insights
    - Error details (if failed)
    """
    api_key_id = api_key.get("id")

    result = await db.execute(
        select(SolarAnalysis).where(
            and_(
                SolarAnalysis.request_id == request_id,
                SolarAnalysis.api_key_id == api_key_id,
            )
        )
    )
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis {request_id} not found or not accessible",
        )

    return AnalysisDetail(
        request_id=analysis.request_id,
        latitude=analysis.latitude,
        longitude=analysis.longitude,
        area_m2=analysis.area_m2,
        tilt=analysis.tilt,
        orientation=analysis.orientation,
        annual_generation_kwh=analysis.annual_generation_kwh,
        monthly_breakdown=analysis.monthly_breakdown,
        peak_month=analysis.peak_month,
        worst_month=analysis.worst_month,
        data_tier=analysis.data_tier,
        confidence_score=analysis.confidence_score,
        ai_insights=analysis.ai_insights,
        status=analysis.status,
        country_code=analysis.country_code,
        applied_plugin=analysis.applied_plugin,
        error_message=analysis.error_message,
        created_at=analysis.created_at.isoformat() if analysis.created_at else "",
        updated_at=analysis.updated_at.isoformat() if analysis.updated_at else "",
    )

