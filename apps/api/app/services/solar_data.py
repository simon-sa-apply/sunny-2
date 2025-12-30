"""
Unified Solar Data Service.

Orchestrates multiple data sources (CAMS, PVGIS) with intelligent
fallback strategy and layered caching to provide global solar radiation coverage.

Cache Strategy:
1. Redis (hot cache) - exact match, short TTL
2. PostgreSQL (warm cache) - proximity search with PostGIS, long TTL
3. External APIs (CAMS/PVGIS) - fetch and cache on miss

Data Source Strategy:
1. Try CAMS first (highest quality satellite data)
2. If CAMS fails (out of coverage), use PVGIS
3. If both fail, use mock data as last resort
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.core.cache import cache, get_cached_model, set_cached_model
from app.core.metrics import log_solar_request, metrics
from app.repositories.cache_repository import cache_repository
from app.services.copernicus import copernicus_service, SolarRadiationData
from app.services.pvgis import pvgis_service, PVGISRadiationData

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSolarData:
    """Unified solar radiation data from any source."""
    
    latitude: float
    longitude: float
    year: int
    
    # Time series or monthly data
    timestamps: Optional[list[datetime]] = None  # Hourly (CAMS)
    monthly_ghi: Optional[dict[str, float]] = None  # Monthly (PVGIS/CAMS)
    
    # Hourly values (only from CAMS)
    ghi: Optional[list[float]] = None
    dni: Optional[list[float]] = None
    dhi: Optional[list[float]] = None
    
    # Annual totals
    annual_ghi_kwh_m2: float = 0.0
    annual_dni_kwh_m2: float = 0.0
    annual_dhi_kwh_m2: float = 0.0
    
    # Optimal configuration
    optimal_tilt: Optional[float] = None
    optimal_azimuth: Optional[float] = None
    
    # Metadata
    source: str = "unknown"
    data_tier: str = "standard"
    elevation: Optional[float] = None
    
    @property
    def has_hourly_data(self) -> bool:
        """Check if hourly time series is available."""
        return self.timestamps is not None and len(self.timestamps) > 0


class SolarDataService:
    """
    Unified service for fetching solar radiation data.
    
    Implements:
    - Layered caching (Redis → PostgreSQL → External APIs)
    - Cascading fallback strategy (CAMS → PVGIS → Mock Data)
    - Automatic cache warming
    """

    # CAMS coverage boundaries (approximate)
    CAMS_LON_MIN = -60
    CAMS_LON_MAX = 150
    CAMS_LAT_MIN = -66
    CAMS_LAT_MAX = 66

    def __init__(self):
        self.cams = copernicus_service
        self.pvgis = pvgis_service
        self.pg_cache = cache_repository

    async def fetch_with_cache(
        self,
        lat: float,
        lon: float,
        year: Optional[int] = None,
    ) -> tuple[UnifiedSolarData, dict[str, Any]]:
        """
        Fetch solar data with layered caching.
        
        Cache hierarchy:
        1. Redis (hot cache) - exact coordinate match
        2. PostgreSQL (warm cache) - proximity search
        3. External APIs - fetch and cache
        
        Returns:
            Tuple of (UnifiedSolarData, cache_info_dict)
        """
        import time
        start_time = time.perf_counter()
        
        if year is None:
            year = datetime.now().year - 1
        
        cache_info = {
            "layer": "miss",
            "source": "unknown",
            "cached": False,
        }
        
        # Layer 1: Redis (hot cache)
        redis_data = await get_cached_model(lat, lon)
        if redis_data:
            cache_info["layer"] = "redis"
            cache_info["cached"] = True
            latency_ms = (time.perf_counter() - start_time) * 1000
            log_solar_request(lat, lon, "redis", True, latency_ms)
            return self._from_cached_model(redis_data, lat, lon, year), cache_info
        
        # Layer 2: PostgreSQL (warm cache with proximity search)
        pg_data = await self.pg_cache.find_nearby(lat, lon)
        if pg_data:
            cache_info["layer"] = "postgresql"
            cache_info["cached"] = True
            cache_info["distance_km"] = pg_data.get("distance_km", 0)
            
            # Warm Redis cache with this result
            model = pg_data.get("interpolation_model", {})
            await set_cached_model(lat, lon, model)
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            log_solar_request(lat, lon, "postgresql", True, latency_ms)
            return self._from_cached_model(pg_data, lat, lon, year), cache_info
        
        # Layer 3: External APIs (cache miss)
        data = await self.fetch_solar_radiation(lat, lon, year)
        cache_info["layer"] = "external"
        cache_info["source"] = data.source
        
        # Cache the result in both layers
        model_data = self._to_cached_model(data)
        
        # Redis (hot cache)
        await set_cached_model(lat, lon, model_data)
        
        # PostgreSQL (warm cache)
        await self.pg_cache.save(
            lat=lat,
            lon=lon,
            interpolation_model=model_data,
            source_dataset=data.source.split()[0],  # e.g., "PVGIS-SARAH2"
            data_tier=data.data_tier,
            country_code=None,  # TODO: detect country
        )
        
        latency_ms = (time.perf_counter() - start_time) * 1000
        log_solar_request(lat, lon, data.source, False, latency_ms)
        
        return data, cache_info

    def _from_cached_model(
        self, 
        cached: dict[str, Any],
        lat: float,
        lon: float,
        year: int,
    ) -> UnifiedSolarData:
        """Convert cached model to UnifiedSolarData."""
        model = cached.get("interpolation_model", cached)
        
        return UnifiedSolarData(
            latitude=lat,
            longitude=lon,
            year=year,
            monthly_ghi=model.get("monthly_ghi"),
            annual_ghi_kwh_m2=model.get("annual_ghi_kwh_m2", 0),
            annual_dni_kwh_m2=model.get("annual_dni_kwh_m2", 0),
            annual_dhi_kwh_m2=model.get("annual_dhi_kwh_m2", 0),
            optimal_tilt=model.get("optimal_tilt"),
            optimal_azimuth=model.get("optimal_azimuth"),
            source=cached.get("source_dataset", "cached"),
            data_tier=cached.get("data_tier", "standard"),
            elevation=model.get("elevation"),
        )

    def _to_cached_model(self, data: UnifiedSolarData) -> dict[str, Any]:
        """Convert UnifiedSolarData to cacheable model dict."""
        return {
            "latitude": data.latitude,
            "longitude": data.longitude,
            "year": data.year,
            "monthly_ghi": data.monthly_ghi,
            "annual_ghi_kwh_m2": data.annual_ghi_kwh_m2,
            "annual_dni_kwh_m2": data.annual_dni_kwh_m2,
            "annual_dhi_kwh_m2": data.annual_dhi_kwh_m2,
            "optimal_tilt": data.optimal_tilt,
            "optimal_azimuth": data.optimal_azimuth,
            "source": data.source,
            "data_tier": data.data_tier,
            "elevation": data.elevation,
        }

    def _is_likely_cams_coverage(self, lat: float, lon: float) -> bool:
        """
        Check if location is likely within CAMS/Meteosat coverage.
        
        CAMS uses Meteosat which covers:
        - Europe, Africa, Middle East
        - Parts of Asia and South America (east)
        
        Excludes:
        - Americas (west of ~60°W)
        - Pacific
        """
        # Western Americas are definitely out
        if lon < -60:
            return False
        
        # Far east Pacific
        if lon > 150:
            return False
            
        # Within general Meteosat field of view
        return True

    async def fetch_solar_radiation(
        self,
        lat: float,
        lon: float,
        year: Optional[int] = None,
    ) -> UnifiedSolarData:
        """
        Fetch solar radiation data with parallel API calls for speed.
        
        OPTIMIZED: Calls CAMS and PVGIS in parallel, uses first successful response.
        This reduces latency from sequential (CAMS_time + PVGIS_time) to max(CAMS_time, PVGIS_time).
        
        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            year: Year to fetch (defaults to previous year)
        
        Returns:
            UnifiedSolarData from the fastest available source
        """
        if year is None:
            year = datetime.now().year - 1
        
        # OPTIMIZATION: Parallel fetch with first-wins strategy
        return await self._fetch_parallel(lat, lon, year)
    
    async def _fetch_parallel(
        self,
        lat: float,
        lon: float,
        year: int,
    ) -> UnifiedSolarData:
        """
        Fetch from CAMS and PVGIS in parallel, return first successful result.
        
        Uses asyncio.wait with FIRST_COMPLETED to minimize latency.
        """
        import asyncio
        
        # Create tasks for both sources
        cams_task = asyncio.create_task(
            self._safe_fetch_cams(lat, lon, year),
            name="cams"
        )
        pvgis_task = asyncio.create_task(
            self._safe_fetch_pvgis(lat, lon, year),
            name="pvgis"
        )
        
        pending = {cams_task, pvgis_task}
        result = None
        errors = []
        
        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=35.0,  # Max wait time
            )
            
            for task in done:
                try:
                    data = task.result()
                    if data is not None:
                        # Got valid data - cancel remaining tasks
                        source = "CAMS" if task.get_name() == "cams" else "PVGIS"
                        logger.info(f"✅ {source} responded first for ({lat}, {lon})")
                        
                        for t in pending:
                            t.cancel()
                        
                        return data
                except Exception as e:
                    errors.append(f"{task.get_name()}: {e}")
                    logger.warning(f"Task {task.get_name()} failed: {e}")
            
            # Timeout reached with no result
            if not done and pending:
                logger.warning(f"Timeout waiting for solar data ({lat}, {lon})")
                for t in pending:
                    t.cancel()
                break
        
        # All sources failed - use mock data
        if errors:
            logger.error(f"All sources failed for ({lat}, {lon}): {errors}")
        
        return self._generate_mock_data(lat, lon, year)
    
    async def _safe_fetch_cams(
        self,
        lat: float,
        lon: float,
        year: int,
    ) -> Optional[UnifiedSolarData]:
        """Safely fetch from CAMS, return None on error."""
        try:
            cams_data = await self.cams.fetch_solar_radiation(lat, lon, year)
            # Only accept real CAMS data, not mock
            if "Real Data" in cams_data.source:
                return self._from_cams(cams_data)
            return None  # Mock data - let PVGIS win
        except Exception as e:
            logger.debug(f"CAMS fetch error: {e}")
            return None
    
    async def _safe_fetch_pvgis(
        self,
        lat: float,
        lon: float,
        year: int,
    ) -> Optional[UnifiedSolarData]:
        """Safely fetch from PVGIS, return None on error."""
        try:
            pvgis_data = await self.pvgis.fetch_solar_radiation(lat, lon, year)
            return self._from_pvgis(pvgis_data)
        except Exception as e:
            logger.debug(f"PVGIS fetch error: {e}")
            return None

    async def _try_cams_then_pvgis(
        self, lat: float, lon: float, year: int
    ) -> UnifiedSolarData:
        """Try CAMS first, fall back to PVGIS."""
        
        # Try CAMS
        try:
            logger.info(f"Attempting CAMS for ({lat}, {lon})")
            cams_data = await self.cams.fetch_solar_radiation(lat, lon, year)
            
            # Check if we got real data (not mock)
            if "Real Data" in cams_data.source:
                logger.info(f"✅ CAMS returned real data for ({lat}, {lon})")
                return self._from_cams(cams_data)
            else:
                # CAMS returned mock data, try PVGIS for better coverage
                logger.info(f"CAMS returned mock data, trying PVGIS for ({lat}, {lon})")
                return await self._try_pvgis(lat, lon, year, fallback_data=cams_data)
                
        except Exception as e:
            logger.warning(f"CAMS failed: {e}, trying PVGIS")
            return await self._try_pvgis(lat, lon, year)

    async def _try_pvgis_then_cams(
        self, lat: float, lon: float, year: int
    ) -> UnifiedSolarData:
        """Try PVGIS first (for Americas), fall back to CAMS."""
        
        try:
            logger.info(f"Attempting PVGIS for ({lat}, {lon}) [Americas strategy]")
            pvgis_data = await self.pvgis.fetch_solar_radiation(lat, lon, year)
            logger.info(f"✅ PVGIS returned data for ({lat}, {lon})")
            return self._from_pvgis(pvgis_data)
            
        except Exception as e:
            logger.warning(f"PVGIS failed: {e}, trying CAMS")
            try:
                cams_data = await self.cams.fetch_solar_radiation(lat, lon, year)
                return self._from_cams(cams_data)
            except Exception as e2:
                logger.error(f"Both sources failed: PVGIS={e}, CAMS={e2}")
                # Return mock data from CAMS as last resort
                return self._generate_mock_data(lat, lon, year)

    async def _try_pvgis(
        self, 
        lat: float, 
        lon: float, 
        year: int,
        fallback_data: Optional[SolarRadiationData] = None,
    ) -> UnifiedSolarData:
        """Try PVGIS, use fallback data if it fails."""
        
        try:
            pvgis_data = await self.pvgis.fetch_solar_radiation(lat, lon, year)
            logger.info(f"✅ PVGIS returned data for ({lat}, {lon})")
            return self._from_pvgis(pvgis_data)
            
        except Exception as e:
            logger.warning(f"PVGIS also failed: {e}")
            
            if fallback_data:
                logger.info("Using CAMS mock data as fallback")
                return self._from_cams(fallback_data)
            
            return self._generate_mock_data(lat, lon, year)

    def _from_cams(self, data: SolarRadiationData) -> UnifiedSolarData:
        """Convert CAMS data to unified format."""
        return UnifiedSolarData(
            latitude=data.latitude,
            longitude=data.longitude,
            year=data.year,
            timestamps=data.timestamps,
            monthly_ghi=data.monthly_ghi,
            ghi=data.ghi,
            dni=data.dni,
            dhi=data.dhi,
            annual_ghi_kwh_m2=data.annual_ghi_kwh_m2,
            annual_dni_kwh_m2=sum(data.dni) / 1000 if data.dni else 0,
            annual_dhi_kwh_m2=sum(data.dhi) / 1000 if data.dhi else 0,
            source=data.source,
            data_tier=data.data_tier,
        )

    def _from_pvgis(self, data: PVGISRadiationData) -> UnifiedSolarData:
        """Convert PVGIS data to unified format."""
        return UnifiedSolarData(
            latitude=data.latitude,
            longitude=data.longitude,
            year=data.year,
            monthly_ghi=data.monthly_ghi,
            annual_ghi_kwh_m2=data.annual_ghi,
            annual_dni_kwh_m2=data.annual_dni,
            annual_dhi_kwh_m2=data.annual_dhi,
            optimal_tilt=data.optimal_tilt,
            optimal_azimuth=data.optimal_azimuth,
            source=data.source,
            data_tier=data.data_tier,
            elevation=data.elevation,
        )

    def _generate_mock_data(self, lat: float, lon: float, year: int) -> UnifiedSolarData:
        """Generate mock data as last resort."""
        import random
        
        # Simple latitude-based model
        lat_factor = 1 - abs(lat) / 90
        base_ghi = 1500 * lat_factor  # kWh/m²/year
        
        # Add some randomness
        annual_ghi = base_ghi * random.uniform(0.9, 1.1)
        
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        
        # Seasonal variation
        monthly_ghi = {}
        for i, month in enumerate(month_names):
            # Southern hemisphere has opposite seasons
            if lat < 0:
                seasonal = 1 + 0.3 * (1 if i in [11, 0, 1] else -0.5 if i in [5, 6, 7] else 0)
            else:
                seasonal = 1 + 0.3 * (1 if i in [5, 6, 7] else -0.5 if i in [11, 0, 1] else 0)
            
            monthly_ghi[month] = (annual_ghi / 12) * seasonal
        
        return UnifiedSolarData(
            latitude=lat,
            longitude=lon,
            year=year,
            monthly_ghi=monthly_ghi,
            annual_ghi_kwh_m2=annual_ghi,
            annual_dni_kwh_m2=annual_ghi * 0.75,
            annual_dhi_kwh_m2=annual_ghi * 0.25,
            optimal_tilt=abs(lat),
            optimal_azimuth=180 if lat > 0 else 0,
            source="Mock Data (fallback)",
            data_tier="estimated",
        )

    async def close(self) -> None:
        """Close all service clients."""
        await self.cams.close()
        await self.pvgis.close()


# Singleton instance
solar_data_service = SolarDataService()

