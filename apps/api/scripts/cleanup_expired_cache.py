"""
Cleanup expired cache entries from PostgreSQL.

This script removes:
1. Expired cached_locations (based on cache_ttl_days)
2. Old error analyses (> 7 days)

Usage:
    python -m scripts.cleanup_expired_cache [--dry-run]

Can be run as:
- Manual cleanup via command line
- Vercel Cron Job via /api/cron/cleanup endpoint
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def cleanup_expired_cache(dry_run: bool = False) -> dict:
    """
    Remove expired cache entries from PostgreSQL.

    Args:
        dry_run: If True, only report what would be deleted

    Returns:
        Dict with cleanup statistics
    """
    from app.core.database import db

    # Initialize database
    db.init()

    results = {
        "expired_locations_deleted": 0,
        "error_analyses_deleted": 0,
        "dry_run": dry_run,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        async with db.session() as session:
            now = datetime.now(timezone.utc)

            # ============================================
            # 1. Find expired cached_locations
            # ============================================
            expired_locations_query = text("""
                SELECT id, latitude, longitude, source_dataset, created_at, cache_ttl_days
                FROM cached_locations
                WHERE created_at < NOW() - INTERVAL '1 day' * cache_ttl_days
            """)

            expired_result = await session.execute(expired_locations_query)
            expired_locations = expired_result.fetchall()

            if dry_run:
                logger.info(f"[DRY RUN] Would delete {len(expired_locations)} expired cached_locations:")
                for loc in expired_locations[:5]:  # Show first 5
                    logger.info(
                        f"  - ID {loc.id}: ({loc.latitude:.4f}, {loc.longitude:.4f}) "
                        f"from {loc.source_dataset}, created {loc.created_at}"
                    )
                if len(expired_locations) > 5:
                    logger.info(f"  ... and {len(expired_locations) - 5} more")
            else:
                if expired_locations:
                    delete_locations_query = text("""
                        DELETE FROM cached_locations
                        WHERE created_at < NOW() - INTERVAL '1 day' * cache_ttl_days
                    """)
                    await session.execute(delete_locations_query)
                    logger.info(f"Deleted {len(expired_locations)} expired cached_locations")

            results["expired_locations_deleted"] = len(expired_locations)

            # ============================================
            # 2. Find old error analyses (> 7 days)
            # ============================================
            error_analyses_query = text("""
                SELECT id, request_id, latitude, longitude, error_message, created_at
                FROM solar_analyses
                WHERE status = 'error'
                  AND created_at < NOW() - INTERVAL '7 days'
            """)

            error_result = await session.execute(error_analyses_query)
            error_analyses = error_result.fetchall()

            if dry_run:
                logger.info(f"[DRY RUN] Would delete {len(error_analyses)} old error analyses:")
                for analysis in error_analyses[:5]:
                    logger.info(
                        f"  - {analysis.request_id}: ({analysis.latitude:.4f}, {analysis.longitude:.4f}) "
                        f"error='{analysis.error_message[:50] if analysis.error_message else 'N/A'}...'"
                    )
                if len(error_analyses) > 5:
                    logger.info(f"  ... and {len(error_analyses) - 5} more")
            else:
                if error_analyses:
                    delete_errors_query = text("""
                        DELETE FROM solar_analyses
                        WHERE status = 'error'
                          AND created_at < NOW() - INTERVAL '7 days'
                    """)
                    await session.execute(delete_errors_query)
                    logger.info(f"Deleted {len(error_analyses)} old error analyses")

            results["error_analyses_deleted"] = len(error_analyses)

            # Commit if not dry run (session auto-commits on exit)
            if not dry_run:
                await session.commit()

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        results["error"] = str(e)
        raise
    finally:
        await db.close()

    # Summary
    if dry_run:
        logger.info(
            f"[DRY RUN] Would delete: "
            f"{results['expired_locations_deleted']} cached_locations, "
            f"{results['error_analyses_deleted']} error analyses"
        )
    else:
        logger.info(
            f"Cleanup completed: "
            f"{results['expired_locations_deleted']} cached_locations, "
            f"{results['error_analyses_deleted']} error analyses deleted"
        )

    return results


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Cleanup expired cache entries from PostgreSQL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(cleanup_expired_cache(dry_run=args.dry_run))
        print(f"\nResult: {result}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

