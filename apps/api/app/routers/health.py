"""Health check and monitoring endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.circuit_breaker import get_all_breakers
from app.core.config import settings
from app.core.database import db
from app.core.metrics import metrics
from app.middleware.rate_limit import get_all_rate_limiters, get_all_semaphores
from app.repositories.cache_repository import cache_repository


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    environment: str
    timestamp: str
    services: dict[str, str]


class MetricsResponse(BaseModel):
    """Metrics response model."""

    timestamp: str
    uptime_seconds: int
    requests: dict[str, Any]
    external_services: dict[str, Any]
    cache: dict[str, Any]
    circuit_breakers: dict[str, Any]
    rate_limiters: dict[str, Any]
    semaphores: dict[str, Any]
    rate_limits_triggered: int


router = APIRouter(prefix="/api")


async def check_database() -> str:
    """Check database connection status."""
    if not db.is_configured:
        return "not_configured"
    try:
        async with db.session() as session:
            await session.execute(text("SELECT 1"))
        return "healthy"
    except Exception as e:
        return f"unhealthy: {str(e)[:50]}"


def check_circuit_breaker_status(breakers: dict) -> dict[str, str]:
    """Get circuit breaker status for health check."""
    result = {}
    for name, breaker in breakers.items():
        state = breaker.state.value
        if state == "open":
            result[name] = "circuit_open"
        elif state == "half_open":
            result[name] = "recovering"
        else:
            result[name] = "healthy"
    return result


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status of the API and its dependent services.
    Includes circuit breaker state for external services.
    """
    # Check actual service status
    db_status = await check_database()

    # Get circuit breaker states
    breakers = get_all_breakers()
    breaker_status = check_circuit_breaker_status(breakers)

    services: dict[str, Any] = {
        "database": db_status,
        "cache": "healthy" if settings.UPSTASH_REDIS_REST_URL else "not_configured",
        "copernicus": (
            breaker_status.get("copernicus", "healthy")
            if settings.COPERNICUS_API_KEY else "not_configured"
        ),
        "pvgis": breaker_status.get("pvgis", "healthy"),
        "gemini": (
            breaker_status.get("gemini", "healthy")
            if settings.GEMINI_API_KEY else "not_configured"
        ),
    }

    # Overall status logic
    overall_status = "healthy"

    if db_status.startswith("unhealthy"):
        overall_status = "degraded"
    elif any(s == "circuit_open" for s in breaker_status.values()):
        overall_status = "degraded"
    elif any(s == "recovering" for s in breaker_status.values()):
        overall_status = "recovering"

    return HealthResponse(
        status=overall_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(UTC).isoformat(),
        services=services,
    )


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get detailed metrics for monitoring and observability.

    Returns:
    - Request counts and latencies
    - External service call statistics
    - Cache hit/miss rates
    - Circuit breaker states
    - Rate limiter status
    - Semaphore utilization

    Use this endpoint for:
    - Dashboard monitoring
    - Alerting thresholds
    - Capacity planning
    """
    # Get base metrics
    metrics_summary = metrics.get_metrics_summary()

    # Get circuit breaker details
    breakers = get_all_breakers()
    circuit_breaker_details = {
        name: breaker.get_status() for name, breaker in breakers.items()
    }

    # Get rate limiter status
    rate_limiter_status = get_all_rate_limiters()

    # Get semaphore status
    semaphore_status = get_all_semaphores()

    return MetricsResponse(
        timestamp=datetime.now(UTC).isoformat(),
        uptime_seconds=metrics_summary.get("uptime_seconds", 0),
        requests=metrics_summary.get("requests", {}),
        external_services=metrics_summary.get("external_services", {}),
        cache=metrics_summary.get("cache", {}),
        circuit_breakers=circuit_breaker_details,
        rate_limiters=rate_limiter_status,
        semaphores=semaphore_status,
        rate_limits_triggered=metrics_summary.get("rate_limits_triggered", 0),
    )


@router.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(breaker_name: str) -> dict[str, Any]:
    """
    Manually reset a circuit breaker.

    Use this endpoint to force a circuit breaker back to closed state
    after confirming the external service is healthy.

    Args:
        breaker_name: Name of the circuit breaker (copernicus, pvgis, gemini)

    Returns:
        Updated circuit breaker status
    """
    breakers = get_all_breakers()

    if breaker_name not in breakers:
        return {
            "error": f"Unknown circuit breaker: {breaker_name}",
            "available": list(breakers.keys()),
        }

    breaker = breakers[breaker_name]
    breaker.reset()

    return {
        "message": f"Circuit breaker '{breaker_name}' reset to CLOSED",
        "status": breaker.get_status(),
    }


@router.get("/cache/stats")
async def get_cache_stats() -> dict[str, Any]:
    """
    Get PostgreSQL cache statistics.

    Returns:
    - Total cached entries
    - Entries by source (CAMS, PVGIS)
    - Entries by data tier (engineering, standard)
    - Expired entries count
    - Cache TTL configuration
    """
    stats = await cache_repository.get_stats()
    return {
        "postgresql_cache": stats,
        "redis_cache": {
            "configured": bool(settings.UPSTASH_REDIS_REST_URL),
            "ttl_seconds": settings.REDIS_TTL_SECONDS,
        },
        "config": {
            "db_cache_ttl_days": settings.DB_CACHE_TTL_DAYS,
            "cache_radius_km": settings.CACHE_RADIUS_KM,
        },
    }


@router.delete("/cache/expired")
async def cleanup_expired_cache() -> dict[str, Any]:
    """
    Clean up expired cache entries from PostgreSQL.

    Returns:
        Number of deleted entries
    """
    deleted_count = await cache_repository.delete_expired()
    return {
        "message": "Cache cleanup completed",
        "deleted_entries": deleted_count,
    }

