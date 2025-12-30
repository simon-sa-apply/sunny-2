"""
Cron job endpoints for scheduled tasks.

These endpoints are designed to be called by Vercel Cron or similar schedulers.
Each endpoint validates the CRON_SECRET before executing.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.repositories.cache_repository import cache_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cron", tags=["Cron Jobs"])


class CleanupResponse(BaseModel):
    """Response from cleanup job."""

    status: str
    expired_locations_deleted: int
    error_analyses_deleted: int
    cache_stats: dict[str, Any]


class HealthCheckResponse(BaseModel):
    """Response from cron health check."""

    status: str
    message: str


async def verify_cron_secret(
    authorization: Optional[str] = Header(None),
) -> bool:
    """
    Verify the cron secret from Authorization header.

    Vercel sends the secret as: Authorization: Bearer <CRON_SECRET>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required for cron jobs",
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Expected: Bearer <token>",
        )

    token = parts[1]

    # For development, accept any token if CRON_SECRET not set
    cron_secret = getattr(settings, "CRON_SECRET", None)
    if cron_secret and token != cron_secret:
        raise HTTPException(
            status_code=403,
            detail="Invalid cron secret",
        )

    return True


@router.get("/cleanup", response_model=CleanupResponse)
async def cron_cleanup(
    authorization: Optional[str] = Header(None),
) -> CleanupResponse:
    """
    Cleanup expired cache entries.

    This endpoint is designed to be called by Vercel Cron.
    Configure in vercel.json:

    ```json
    {
      "crons": [
        {
          "path": "/api/cron/cleanup",
          "schedule": "0 3 * * *"
        }
      ]
    }
    ```

    Runs daily at 3 AM UTC to:
    - Delete expired cached_locations
    - Delete old error analyses (> 7 days)

    Returns:
        Cleanup statistics
    """
    await verify_cron_secret(authorization)

    logger.info("Starting scheduled cache cleanup...")

    try:
        from sqlalchemy import text
        from app.core.database import db

        expired_locations = 0
        error_analyses = 0

        async with db.session() as session:
            # Delete expired cached_locations
            delete_locations = text("""
                DELETE FROM cached_locations
                WHERE created_at < NOW() - INTERVAL '1 day' * cache_ttl_days
                RETURNING id
            """)
            result = await session.execute(delete_locations)
            expired_locations = len(result.fetchall())

            # Delete old error analyses
            delete_errors = text("""
                DELETE FROM solar_analyses
                WHERE status = 'error'
                  AND created_at < NOW() - INTERVAL '7 days'
                RETURNING id
            """)
            result = await session.execute(delete_errors)
            error_analyses = len(result.fetchall())

            await session.commit()

        # Get current cache stats
        cache_stats = await cache_repository.get_stats()

        logger.info(
            f"Cleanup completed: {expired_locations} locations, "
            f"{error_analyses} error analyses deleted"
        )

        return CleanupResponse(
            status="ok",
            expired_locations_deleted=expired_locations,
            error_analyses_deleted=error_analyses,
            cache_stats=cache_stats,
        )

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}",
        )


@router.get("/health", response_model=HealthCheckResponse)
async def cron_health(
    authorization: Optional[str] = Header(None),
) -> HealthCheckResponse:
    """
    Health check endpoint for cron monitoring.

    Can be used to verify cron jobs are working correctly.
    """
    await verify_cron_secret(authorization)

    return HealthCheckResponse(
        status="ok",
        message="Cron system is operational",
    )


@router.get("/cache-stats")
async def get_cache_stats(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    """
    Get current cache statistics.

    Returns detailed information about the PostgreSQL cache:
    - Total entries
    - Entries by source (CAMS, PVGIS)
    - Entries by tier (engineering, standard)
    - Expired entries count
    """
    await verify_cron_secret(authorization)

    try:
        stats = await cache_repository.get_stats()
        return {
            "status": "ok",
            "stats": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}",
        )

