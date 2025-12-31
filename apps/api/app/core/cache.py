"""
Redis Cache Management for sunny-2 API.

Provides a two-tier caching strategy:
1. Redis (hot cache): Fast, short-lived, exact matches
2. PostgreSQL (warm cache): Slower, long-lived, proximity matches

Uses Upstash Redis REST API for serverless-friendly caching.
"""

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.core.metrics import log_cache_operation, metrics

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis cache manager for storing and retrieving solar data.

    Features:
    - Serverless-friendly (Upstash Redis REST API)
    - Configurable TTL per cache type
    - Metrics collection for monitoring
    - Graceful degradation when Redis unavailable
    """

    def __init__(self) -> None:
        self._client: Any | None = None
        self._initialized = False

    @property
    def is_configured(self) -> bool:
        """Check if Redis is configured."""
        return bool(
            settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN
        )

    @property
    def is_initialized(self) -> bool:
        """Check if Redis client is initialized."""
        return self._initialized

    def init(self) -> None:
        """Initialize the Redis client."""
        if not self.is_configured:
            logger.warning("Redis not configured, caching disabled")
            return

        try:
            from upstash_redis import Redis

            self._client = Redis(
                url=settings.UPSTASH_REDIS_REST_URL,
                token=settings.UPSTASH_REDIS_REST_TOKEN,
            )
            self._initialized = True
            logger.info("Redis cache initialized successfully")
        except ImportError:
            logger.warning("upstash-redis not installed, caching disabled")
            self._initialized = False
        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            self._initialized = False

    async def get(self, key: str) -> str | None:
        """
        Get a value from cache.

        Records metrics for monitoring cache hit rate.
        """
        if not self._initialized or not self._client:
            return None

        start_time = time.perf_counter()
        try:
            result = self._client.get(key)
            latency_ms = (time.perf_counter() - start_time) * 1000

            hit = result is not None
            log_cache_operation("redis", "get", key, hit, latency_ms)

            return result
        except Exception as e:
            logger.error(f"Cache get error for key '{key[:50]}': {e}")
            metrics.record_cache_miss("redis")
            return None

    async def set(
        self,
        key: str,
        value: str,
        ex: int | None = None,
    ) -> bool:
        """
        Set a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ex: TTL in seconds (default from settings)
        """
        if not self._initialized or not self._client:
            return False

        if ex is None:
            ex = settings.REDIS_TTL_SECONDS

        start_time = time.perf_counter()
        try:
            self._client.setex(key, ex, value)
            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.debug(
                f"Cache SET: key={key[:50]} ttl={ex}s latency={latency_ms:.2f}ms"
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key[:50]}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        if not self._initialized or not self._client:
            return False
        try:
            self._client.delete(key)
            logger.debug(f"Cache DELETE: key={key[:50]}")
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key '{key[:50]}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        if not self._initialized or not self._client:
            return False
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds."""
        if not self._initialized or not self._client:
            return -1
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error: {e}")
            return -1

    def _make_cache_key(
        self,
        lat: float,
        lon: float,
        precision: int = 2,
        prefix: str = "solar",
    ) -> str:
        """
        Create a cache key from coordinates.

        Rounds coordinates to specified precision to enable cache hits
        for nearby locations (effectively creating a grid).

        Args:
            lat: Latitude (-90 to 90)
            lon: Longitude (-180 to 180)
            precision: Decimal places for rounding
                - 2 = ~1.11km grid at equator
                - 1 = ~11.1km grid at equator
            prefix: Cache key prefix for namespacing

        Returns:
            Cache key string
        """
        rounded_lat = round(lat, precision)
        rounded_lon = round(lon, precision)
        return f"{prefix}:{rounded_lat}:{rounded_lon}"

    def get_status(self) -> dict[str, Any]:
        """Get cache status for health checks."""
        return {
            "configured": self.is_configured,
            "initialized": self.is_initialized,
            "ttl_seconds": settings.REDIS_TTL_SECONDS,
        }


# ===========================================
# Cache Key Generators
# ===========================================

def make_solar_key(lat: float, lon: float, year: int = 2023) -> str:
    """Generate cache key for solar radiation data."""
    return f"solar:{round(lat, 2)}:{round(lon, 2)}:{year}"


def make_model_key(lat: float, lon: float) -> str:
    """Generate cache key for interpolation model."""
    return f"model:{round(lat, 2)}:{round(lon, 2)}"


def make_geosearch_key(query: str) -> str:
    """Generate cache key for geosearch results."""
    # Normalize query for caching
    normalized = query.lower().strip()[:100]
    return f"geo:{normalized}"


# ===========================================
# Helper Functions
# ===========================================

async def get_cached_model(
    lat: float,
    lon: float,
    radius_km: float = 5.0,
) -> dict[str, Any] | None:
    """
    Get cached interpolation model for a location.

    Uses coordinate rounding to find cache hits within approximate radius.

    Args:
        lat: Latitude
        lon: Longitude
        radius_km: Search radius (approximated by rounding precision)

    Returns:
        Cached interpolation model or None
    """
    # Determine precision based on radius
    # precision 2 ≈ 1.11km at equator
    # precision 1 ≈ 11.1km at equator
    precision = 2 if radius_km <= 5 else 1

    cache_key = cache._make_cache_key(lat, lon, precision, prefix="model")
    cached = await cache.get(cache_key)

    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in cache for key: {cache_key}")
            return None

    return None


async def set_cached_model(
    lat: float,
    lon: float,
    model: dict[str, Any],
    ttl_days: int | None = None,
) -> bool:
    """
    Cache an interpolation model for a location.

    Args:
        lat: Latitude
        lon: Longitude
        model: Interpolation model data
        ttl_days: Cache TTL in days (default from settings)

    Returns:
        True if cached successfully
    """
    if ttl_days is None:
        ttl_days = settings.DB_CACHE_TTL_DAYS

    cache_key = cache._make_cache_key(lat, lon, precision=2, prefix="model")
    model_json = json.dumps(model)
    ttl_seconds = ttl_days * 86400

    return await cache.set(cache_key, model_json, ex=ttl_seconds)


async def get_cached_solar_data(
    lat: float,
    lon: float,
    year: int,
) -> dict[str, Any] | None:
    """Get cached solar radiation data."""
    cache_key = make_solar_key(lat, lon, year)
    cached = await cache.get(cache_key)

    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            return None

    return None


async def set_cached_solar_data(
    lat: float,
    lon: float,
    year: int,
    data: dict[str, Any],
    ttl_seconds: int | None = None,
) -> bool:
    """Cache solar radiation data."""
    if ttl_seconds is None:
        ttl_seconds = settings.REDIS_TTL_SECONDS

    cache_key = make_solar_key(lat, lon, year)
    data_json = json.dumps(data, default=str)

    return await cache.set(cache_key, data_json, ex=ttl_seconds)


# Global cache instance
cache = CacheManager()

