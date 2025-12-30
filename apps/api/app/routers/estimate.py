"""Solar estimation API endpoints."""

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.core.config import settings
from app.plugins.base import get_plugin_for_location
from app.schemas.estimate import EstimateRequest, EstimateResponse, LocationInfo, OptimizationInfo, SavingsInfo
from app.services.cache_manager import get_or_create_model
from app.services.copernicus import copernicus_service
from app.services.ai_consultant import ai_consultant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Estimation"])


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    summary="Calculate solar generation potential",
    description="""
    Calculate the solar generation potential for a given location and panel configuration.
    
    Returns:
    - Annual and monthly generation estimates in kWh
    - Peak and worst months for planning
    - Optimization recommendations
    - Economic savings (if country plugin available)
    - Confidence score based on data quality
    """,
)
async def create_estimate(
    request: EstimateRequest,
    response: Response,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> EstimateResponse:
    """
    Create a solar generation estimate.
    
    This endpoint:
    1. Validates input parameters
    2. Fetches/caches solar radiation data from Copernicus
    3. Generates interpolation model for the location
    4. Calculates generation based on panel parameters
    5. Applies country-specific regulations if available
    """
    request_id = str(uuid.uuid4())
    
    logger.info(
        f"Estimate request {request_id}: ({request.lat}, {request.lon}) "
        f"area={request.area_m2}m²"
    )
    
    try:
        # 1. Get or create interpolation model
        model = await get_or_create_model(
            lat=request.lat,
            lon=request.lon,
            area_m2=request.area_m2,
            panel_efficiency=request.panel_efficiency or 0.22,
        )
        
        # 2. Determine tilt and orientation
        tilt = request.tilt if request.tilt is not None else model.optimal_tilt
        orientation = (
            _orientation_to_degrees(request.orientation)
            if request.orientation and request.orientation != "auto"
            else model.optimal_orientation
        )
        
        # 3. Interpolate for requested parameters
        result = model.interpolate(tilt=tilt, orientation=orientation)
        
        # 4. Get country plugin
        plugin = get_plugin_for_location(request.lat, request.lon)
        country_code = plugin.constants.country_code
        data_tier = plugin.constants.data_tier if country_code != "GLOBAL" else model.data_tier
        
        # 5. Calculate savings
        savings = None
        if result["annual_generation_kwh"] > 0:
            savings_data = plugin.calculate_savings(
                generation_kwh=result["annual_generation_kwh"],
                custom_price=request.electricity_price,
            )
            savings = SavingsInfo(**savings_data)
        
        # 6. Generate AI insights (optional - skip for faster response)
        ai_insights = None
        if request.include_ai_insights:
            try:
                calculation_data = {
                    **result,
                    "data_tier": data_tier,
                    "location": {
                        "lat": request.lat,
                        "lon": request.lon,
                        "country_code": country_code if country_code != "GLOBAL" else None,
                    },
                }
                ai_insights = await ai_consultant.generate_narrative(
                    calculation_data=calculation_data,
                    country_plugin=plugin.constants.regulatory_reference,
                )
                logger.info(f"Generated AI insights for {request_id}")
            except Exception as e:
                logger.warning(f"Failed to generate AI insights for {request_id}: {e}")
                # Continue without AI insights - they're optional
        else:
            logger.info(f"Skipping AI insights for {request_id} (fast mode)")
        
        # 7. Build response
        response_data = EstimateResponse(
            annual_generation_kwh=result["annual_generation_kwh"],
            monthly_breakdown=result["monthly_breakdown"],
            peak_month=result["peak_month"],
            worst_month=result["worst_month"],
            location=LocationInfo(
                lat=request.lat,
                lon=request.lon,
                country_code=country_code if country_code != "GLOBAL" else None,
                data_tier=data_tier,
            ),
            data_tier=data_tier,
            confidence_score=0.9 if data_tier == "engineering" else 0.75,
            optimization=OptimizationInfo(
                current_tilt=tilt,
                current_orientation=orientation,
                optimal_tilt=model.optimal_tilt,
                optimal_orientation=model.optimal_orientation,
                efficiency_vs_optimal=result["efficiency_vs_optimal"],
                optimal_annual_kwh=model.optimal_annual_kwh,
            ),
            savings=savings,
            applied_plugin=plugin.constants.regulatory_reference,
            ai_insights=ai_insights,
            request_id=request_id,
        )
        
        # Set response headers
        response.headers["X-Data-Tier"] = data_tier
        response.headers["X-Confidence-Score"] = str(response_data.confidence_score)
        response.headers["X-Request-ID"] = request_id
        
        return response_data
        
    except ValueError as e:
        logger.warning(f"Validation error for {request_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "type": "validation_error",
                "title": "Invalid request parameters",
                "detail": str(e),
                "instance": f"/api/v1/estimate/{request_id}",
            },
        )
    except Exception as e:
        logger.error(f"Error processing {request_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "type": "internal_error",
                "title": "Processing error",
                "detail": "An error occurred while processing your request",
                "instance": f"/api/v1/estimate/{request_id}",
            },
        )


@router.post(
    "/interpolate",
    summary="Quick interpolation for existing model",
    description="Interpolate values for a location that already has a cached model.",
)
async def interpolate(
    lat: float,
    lon: float,
    tilt: float,
    orientation: float,
    area_m2: float = 15.0,
) -> dict[str, Any]:
    """
    Quick interpolation endpoint for the Solar Clock feature.
    
    Assumes the model is already cached. Returns error if not.
    Designed for <200ms response time.
    """
    try:
        model = await get_or_create_model(lat, lon, area_m2)
        return model.interpolate(tilt, orientation)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=f"No cached model found for ({lat}, {lon}). Call /estimate first.",
        )


def _orientation_to_degrees(orientation: Optional[str]) -> float:
    """Convert cardinal orientation to degrees."""
    mapping = {
        "N": 0,
        "NE": 45,
        "E": 90,
        "SE": 135,
        "S": 180,
        "SW": 225,
        "W": 270,
        "NW": 315,
    }
    return mapping.get(orientation.upper() if orientation else "S", 180)

