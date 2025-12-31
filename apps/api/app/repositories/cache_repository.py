"""
CacheRepository: PostgreSQL warm cache for interpolation models.

This repository provides geospatial caching using PostGIS, enabling:
- Proximity-based cache lookups (find cached model within X km)
- Long-term persistence (30+ days vs Redis hours)
- Efficient geospatial indexing with GIST

Cache Strategy:
    1. Redis (hot cache)  → Fast, short TTL, exact matches
    2. PostgreSQL (warm)  → PostGIS proximity search, long TTL
    3. External APIs      → CAMS/PVGIS as fallback
"""

import logging
import time
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db
from app.core.metrics import log_cache_operation, metrics
from app.models.solar_analysis import CachedLocation

logger = logging.getLogger(__name__)


class CacheRepository:
    """
    Repository for managing cached interpolation models in PostgreSQL.

    Uses PostGIS for efficient geospatial queries:
    - ST_DWithin for proximity search
    - ST_Distance for sorting by distance
    - GIST index for fast spatial lookups

    Example:
        >>> repo = CacheRepository()
        >>> model = await repo.find_nearby(-33.45, -70.65, radius_km=5.0)
        >>> if model:
        ...     print("Cache hit!")
        ... else:
        ...     # Fetch from external API and cache it
        ...     await repo.save(-33.45, -70.65, interpolation_model, "PVGIS")
    """

    def __init__(self) -> None:
        self._has_postgis = True  # Assume PostGIS is available

    async def find_nearby(
        self,
        lat: float,
        lon: float,
        radius_km: float = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Find a cached interpolation model near the given coordinates.

        Uses PostGIS ST_DWithin for efficient proximity search with GIST index.
        Falls back to bounding box search if PostGIS is unavailable.

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            radius_km: Search radius in kilometers (default from settings)
            session: Optional existing database session

        Returns:
            Cached interpolation model dict, or None if not found
        """
        if radius_km is None:
            radius_km = settings.CACHE_RADIUS_KM

        start_time = time.perf_counter()

        try:
            if session:
                result = await self._find_nearby_impl(session, lat, lon, radius_km)
            else:
                async with db.session() as session:
                    result = await self._find_nearby_impl(session, lat, lon, radius_km)

            latency_ms = (time.perf_counter() - start_time) * 1000
            hit = result is not None

            log_cache_operation(
                layer="postgresql",
                operation="find_nearby",
                key=f"{lat:.2f},{lon:.2f}",
                hit=hit,
                latency_ms=latency_ms,
            )

            if hit:
                logger.debug(
                    f"PostgreSQL cache HIT: ({lat:.4f}, {lon:.4f}) "
                    f"within {radius_km}km, latency={latency_ms:.2f}ms"
                )

            return result

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Cache find_nearby error: {e}")
            metrics.record_cache_error("postgresql")
            return None

    async def _find_nearby_impl(
        self,
        session: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any] | None:
        """Internal implementation of find_nearby."""

        # Try PostGIS query first
        if self._has_postgis:
            try:
                return await self._find_with_postgis(session, lat, lon, radius_km)
            except Exception as e:
                if "geometry" in str(e).lower() or "st_" in str(e).lower():
                    logger.warning(f"PostGIS not available, falling back to bbox: {e}")
                    self._has_postgis = False
                else:
                    raise

        # Fallback to bounding box search
        return await self._find_with_bbox(session, lat, lon, radius_km)

    async def _find_with_postgis(
        self,
        session: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any] | None:
        """Find nearby location using PostGIS ST_DWithin."""

        # Convert km to degrees (approximate at equator: 1° ≈ 111km)
        # More accurate conversion considering latitude
        radius_km / (111.32 * abs(lat) / 90 + 111.32 * (90 - abs(lat)) / 90)

        # Use raw SQL for PostGIS query (more reliable across different setups)
        query = text("""
            SELECT
                id,
                latitude,
                longitude,
                interpolation_model,
                data_tier,
                source_dataset,
                country_code,
                cache_ttl_days,
                created_at,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) / 1000 as distance_km
            FROM cached_locations
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius_m
            )
            AND created_at > NOW() - INTERVAL '1 day' * :ttl_days
            ORDER BY distance_km ASC
            LIMIT 1
        """)

        result = await session.execute(
            query,
            {
                "lat": lat,
                "lon": lon,
                "radius_m": radius_km * 1000,  # Convert to meters
                "ttl_days": settings.DB_CACHE_TTL_DAYS,
            }
        )

        row = result.fetchone()

        if row:
            return {
                "id": row.id,
                "latitude": row.latitude,
                "longitude": row.longitude,
                "interpolation_model": row.interpolation_model,
                "data_tier": row.data_tier,
                "source_dataset": row.source_dataset,
                "country_code": row.country_code,
                "distance_km": row.distance_km,
                "cached_at": row.created_at.isoformat() if row.created_at else None,
            }

        return None

    async def _find_with_bbox(
        self,
        session: AsyncSession,
        lat: float,
        lon: float,
        radius_km: float,
    ) -> dict[str, Any] | None:
        """
        Fallback: Find nearby location using bounding box.

        Less accurate than PostGIS but works without PostGIS extension.
        """
        # Convert radius to approximate degree bounds
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        import math

        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * math.cos(math.radians(lat)))

        min_lat = lat - lat_offset
        max_lat = lat + lat_offset
        min_lon = lon - lon_offset
        max_lon = lon + lon_offset

        query = (
            select(CachedLocation)
            .where(
                CachedLocation.latitude.between(min_lat, max_lat),
                CachedLocation.longitude.between(min_lon, max_lon),
            )
            .order_by(
                # Approximate distance sorting
                func.abs(CachedLocation.latitude - lat) +
                func.abs(CachedLocation.longitude - lon)
            )
            .limit(1)
        )

        result = await session.execute(query)
        cached = result.scalar_one_or_none()

        if cached and not cached.is_expired():
            # Calculate approximate distance
            distance_km = (
                ((cached.latitude - lat) ** 2 +
                 (cached.longitude - lon) ** 2) ** 0.5 * 111.0
            )

            return {
                "id": cached.id,
                "latitude": cached.latitude,
                "longitude": cached.longitude,
                "interpolation_model": cached.interpolation_model,
                "data_tier": cached.data_tier,
                "source_dataset": cached.source_dataset,
                "country_code": cached.country_code,
                "distance_km": distance_km,
                "cached_at": cached.created_at.isoformat() if cached.created_at else None,
            }

        return None

    async def save(
        self,
        lat: float,
        lon: float,
        interpolation_model: dict[str, Any],
        source_dataset: str = "PVGIS",
        data_tier: str = "standard",
        country_code: str | None = None,
        session: AsyncSession | None = None,
    ) -> int | None:
        """
        Save an interpolation model to the PostgreSQL cache.

        Creates a PostGIS POINT geometry for efficient spatial queries.

        Args:
            lat: Latitude
            lon: Longitude
            interpolation_model: The pre-computed interpolation model
            source_dataset: Data source (CAMS, PVGIS, ERA5)
            data_tier: Quality tier (engineering, standard)
            country_code: ISO country code
            session: Optional existing database session

        Returns:
            The ID of the cached record, or None on failure
        """
        start_time = time.perf_counter()

        try:
            if session:
                result = await self._save_impl(
                    session, lat, lon, interpolation_model,
                    source_dataset, data_tier, country_code
                )
            else:
                async with db.session() as session:
                    result = await self._save_impl(
                        session, lat, lon, interpolation_model,
                        source_dataset, data_tier, country_code
                    )

            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"PostgreSQL cache SAVE: ({lat:.4f}, {lon:.4f}) "
                f"source={source_dataset}, latency={latency_ms:.2f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Cache save error: {e}")
            metrics.record_cache_error("postgresql")
            return None

    async def _save_impl(
        self,
        session: AsyncSession,
        lat: float,
        lon: float,
        interpolation_model: dict[str, Any],
        source_dataset: str,
        data_tier: str,
        country_code: str | None,
    ) -> int:
        """Internal implementation of save."""
        import json

        model_json = json.dumps(interpolation_model)

        # Use raw SQL to handle PostGIS geometry
        # Note: asyncpg uses $1, $2, etc. placeholders, but SQLAlchemy text()
        # with bindparams converts :name to $ placeholders automatically
        if self._has_postgis:
            query = text("""
                INSERT INTO cached_locations
                    (latitude, longitude, geom, interpolation_model,
                     source_dataset, data_tier, country_code, cache_ttl_days,
                     created_at, updated_at)
                VALUES
                    (:lat, :lon, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                     CAST(:model AS jsonb), :source, :tier, :country, :ttl,
                     NOW(), NOW())
                ON CONFLICT (latitude, longitude)
                DO UPDATE SET
                    interpolation_model = CAST(EXCLUDED.interpolation_model AS jsonb),
                    source_dataset = EXCLUDED.source_dataset,
                    data_tier = EXCLUDED.data_tier,
                    updated_at = NOW()
                RETURNING id
            """).bindparams(
                lat=lat,
                lon=lon,
                model=model_json,
                source=source_dataset,
                tier=data_tier,
                country=country_code,
                ttl=settings.DB_CACHE_TTL_DAYS,
            )
        else:
            # Fallback without PostGIS geometry
            query = text("""
                INSERT INTO cached_locations
                    (latitude, longitude, interpolation_model,
                     source_dataset, data_tier, country_code, cache_ttl_days,
                     created_at, updated_at)
                VALUES
                    (:lat, :lon, CAST(:model AS jsonb), :source, :tier, :country, :ttl,
                     NOW(), NOW())
                ON CONFLICT (latitude, longitude)
                DO UPDATE SET
                    interpolation_model = CAST(EXCLUDED.interpolation_model AS jsonb),
                    source_dataset = EXCLUDED.source_dataset,
                    data_tier = EXCLUDED.data_tier,
                    updated_at = NOW()
                RETURNING id
            """).bindparams(
                lat=lat,
                lon=lon,
                model=model_json,
                source=source_dataset,
                tier=data_tier,
                country=country_code,
                ttl=settings.DB_CACHE_TTL_DAYS,
            )

        result = await session.execute(query)
        row = result.fetchone()
        return row.id if row else None

    async def delete_expired(
        self,
        session: AsyncSession | None = None,
    ) -> int:
        """
        Delete expired cache entries.

        Returns:
            Number of deleted entries
        """
        try:
            if session:
                return await self._delete_expired_impl(session)
            else:
                async with db.session() as session:
                    return await self._delete_expired_impl(session)
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            return 0

    async def _delete_expired_impl(self, session: AsyncSession) -> int:
        """Internal implementation of delete_expired."""

        query = text("""
            DELETE FROM cached_locations
            WHERE created_at < NOW() - INTERVAL '1 day' * cache_ttl_days
            RETURNING id
        """)

        result = await session.execute(query)
        deleted = result.fetchall()
        count = len(deleted)

        if count > 0:
            logger.info(f"Cache cleanup: deleted {count} expired entries")

        return count

    async def get_stats(
        self,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (count, oldest, newest, by source, etc.)
        """
        try:
            if session:
                return await self._get_stats_impl(session)
            else:
                async with db.session() as session:
                    return await self._get_stats_impl(session)
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}

    async def _get_stats_impl(self, session: AsyncSession) -> dict[str, Any]:
        """Internal implementation of get_stats."""

        # Total count and date range
        count_query = text("""
            SELECT
                COUNT(*) as total,
                MIN(created_at) as oldest,
                MAX(created_at) as newest
            FROM cached_locations
        """)

        result = await session.execute(count_query)
        row = result.fetchone()

        # Count by source
        source_query = text("""
            SELECT source_dataset, COUNT(*) as count
            FROM cached_locations
            GROUP BY source_dataset
        """)

        source_result = await session.execute(source_query)
        sources = {r.source_dataset: r.count for r in source_result.fetchall()}

        # Count by tier
        tier_query = text("""
            SELECT data_tier, COUNT(*) as count
            FROM cached_locations
            GROUP BY data_tier
        """)

        tier_result = await session.execute(tier_query)
        tiers = {r.data_tier: r.count for r in tier_result.fetchall()}

        # Expired count
        expired_query = text("""
            SELECT COUNT(*) as count
            FROM cached_locations
            WHERE created_at < NOW() - INTERVAL '1 day' * cache_ttl_days
        """)

        expired_result = await session.execute(expired_query)
        expired_row = expired_result.fetchone()

        return {
            "total_entries": row.total if row else 0,
            "oldest_entry": row.oldest.isoformat() if row and row.oldest else None,
            "newest_entry": row.newest.isoformat() if row and row.newest else None,
            "by_source": sources,
            "by_tier": tiers,
            "expired_entries": expired_row.count if expired_row else 0,
            "ttl_days": settings.DB_CACHE_TTL_DAYS,
        }

    async def find_by_id(
        self,
        cache_id: int,
        session: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Find a cached entry by ID.

        Args:
            cache_id: The cache entry ID
            session: Optional existing database session

        Returns:
            Cached entry dict or None
        """
        try:
            if session:
                return await self._find_by_id_impl(session, cache_id)
            else:
                async with db.session() as session:
                    return await self._find_by_id_impl(session, cache_id)
        except Exception as e:
            logger.error(f"Cache find_by_id error: {e}")
            return None

    async def _find_by_id_impl(
        self,
        session: AsyncSession,
        cache_id: int,
    ) -> dict[str, Any] | None:
        """Internal implementation of find_by_id."""

        query = select(CachedLocation).where(CachedLocation.id == cache_id)
        result = await session.execute(query)
        cached = result.scalar_one_or_none()

        if cached:
            return {
                "id": cached.id,
                "latitude": cached.latitude,
                "longitude": cached.longitude,
                "interpolation_model": cached.interpolation_model,
                "data_tier": cached.data_tier,
                "source_dataset": cached.source_dataset,
                "country_code": cached.country_code,
                "cached_at": cached.created_at.isoformat() if cached.created_at else None,
                "is_expired": cached.is_expired(),
            }

        return None


# Global repository instance
cache_repository = CacheRepository()

