"""
Geographic Cache Manager.

Implements layered caching strategy for solar interpolation models:
1. Redis (hot cache) - exact match, fast, short TTL
2. PostgreSQL (warm cache) - proximity search with PostGIS, long TTL
3. External APIs (CAMS/PVGIS) - fetch and cache on miss
"""

import logging

from app.core.cache import cache, get_cached_model, set_cached_model
from app.repositories.cache_repository import cache_repository
from app.services.interpolation import InterpolationModel, generate_interpolation_model
from app.services.solar_data import solar_data_service

logger = logging.getLogger(__name__)


async def get_or_create_model(
    lat: float,
    lon: float,
    area_m2: float = 15.0,
    panel_efficiency: float = 0.22,
) -> InterpolationModel:
    """
    Get cached interpolation model or create new one.

    Implements layered caching strategy:
    1. Check Redis (hot cache) for exact coordinate match
    2. Check PostgreSQL (warm cache) for nearby coordinates (PostGIS)
    3. If cache miss, fetch from external APIs and generate model
    4. Cache the new model in both Redis and PostgreSQL

    Args:
        lat: Latitude
        lon: Longitude
        area_m2: Panel area in square meters
        panel_efficiency: Panel efficiency (0.18-0.25)

    Returns:
        InterpolationModel ready for use
    """
    # Layer 1: Redis (hot cache) - exact match
    cached_data = await get_cached_model(lat, lon, radius_km=5.0)

    if cached_data:
        logger.info(f"Redis cache HIT for ({lat}, {lon})")
        cached_model = InterpolationModel(**cached_data)
        return _maybe_scale_model(cached_model, area_m2)

    # Layer 2: PostgreSQL (warm cache) - proximity search
    pg_cached = await cache_repository.find_nearby(lat, lon)

    if pg_cached:
        logger.info(
            f"PostgreSQL cache HIT for ({lat}, {lon}) - "
            f"distance={pg_cached.get('distance_km', 0):.2f}km"
        )

        model_data = pg_cached.get("interpolation_model", {})

        # Warm Redis with this result
        await set_cached_model(lat, lon, model_data)

        cached_model = InterpolationModel(**model_data)
        return _maybe_scale_model(cached_model, area_m2)

    # Layer 3: External APIs (cache miss)
    logger.info(f"Cache MISS for ({lat}, {lon}), fetching from external APIs")

    # Use unified solar data service (CAMS → PVGIS → Mock)
    solar_data = await solar_data_service.fetch_solar_radiation(lat, lon)

    # Generate interpolation model
    model = generate_interpolation_model(
        solar_data=solar_data,
        area_m2=area_m2,
        panel_efficiency=panel_efficiency,
    )

    model_dict = model.to_dict()

    # Cache in Redis (hot cache)
    await set_cached_model(lat, lon, model_dict, ttl_days=30)

    # Cache in PostgreSQL (warm cache) with PostGIS geometry
    await cache_repository.save(
        lat=lat,
        lon=lon,
        interpolation_model=model_dict,
        source_dataset=solar_data.source.split()[0],  # e.g., "PVGIS-SARAH2"
        data_tier=solar_data.data_tier,
    )

    logger.info(f"Cached new model for ({lat}, {lon}) in both Redis and PostgreSQL")

    return model


def _maybe_scale_model(model: InterpolationModel, target_area: float) -> InterpolationModel:
    """Scale model to target area if different from cached area."""
    if model.area_m2 != target_area:
        scale_factor = target_area / model.area_m2
        logger.info(f"Scaling cached model: {model.area_m2}m² -> {target_area}m²")
        return _scale_model(model, scale_factor, target_area)
    return model


def _scale_model(
    model: InterpolationModel,
    scale_factor: float,
    new_area: float,
) -> InterpolationModel:
    """Scale a cached model to a different area size."""
    # Scale all values
    scaled_monthly = [
        [[v * scale_factor for v in month] for month in orient]
        for orient in model.monthly_values
    ]
    scaled_annual = [
        [v * scale_factor for v in orient]
        for orient in model.annual_values
    ]

    return InterpolationModel(
        latitude=model.latitude,
        longitude=model.longitude,
        tilts=model.tilts,
        orientations=model.orientations,
        monthly_values=scaled_monthly,
        annual_values=scaled_annual,
        optimal_tilt=model.optimal_tilt,
        optimal_orientation=model.optimal_orientation,
        optimal_annual_kwh=model.optimal_annual_kwh * scale_factor,
        area_m2=new_area,
        panel_efficiency=model.panel_efficiency,
        data_tier=model.data_tier,
        year=model.year,
    )


async def invalidate_cache(lat: float, lon: float) -> bool:
    """Invalidate cache for a specific location."""
    cache_key = cache._make_cache_key(lat, lon)
    return await cache.delete(cache_key)

