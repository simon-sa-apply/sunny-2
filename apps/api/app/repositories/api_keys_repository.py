"""
API Keys Repository.

Provides CRUD operations for API key management.
"""

import logging
import secrets
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import db
from app.models.api_keys import ApiKey

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


class ApiKeysRepository:
    """
    Repository for managing API keys.

    Provides:
    - Create new API keys
    - Validate and lookup keys
    - Update key settings
    - Deactivate/delete keys
    - Usage tracking
    """

    async def create(
        self,
        name: str,
        description: str | None = None,
        owner_email: str | None = None,
        rate_limit_per_minute: int = 100,
        rate_limit_per_day: int = 10000,
        expires_at: datetime | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """
        Create a new API key.

        Args:
            name: Descriptive name for the key
            description: Optional description
            owner_email: Email of key owner
            rate_limit_per_minute: Max requests per minute
            rate_limit_per_day: Max requests per day
            expires_at: Optional expiration datetime
            session: Optional existing database session

        Returns:
            Dict with key details (including the raw key - only shown once!)
        """
        raw_key = generate_api_key()

        async def _create(s: AsyncSession) -> dict[str, Any]:
            api_key = ApiKey(
                key=raw_key,
                name=name,
                description=description,
                owner_email=owner_email,
                rate_limit_per_minute=rate_limit_per_minute,
                rate_limit_per_day=rate_limit_per_day,
                expires_at=expires_at,
                is_active=True,
                total_requests=0,
            )
            s.add(api_key)
            await s.flush()

            logger.info(f"Created API key '{name}' (id={api_key.id})")

            return {
                "id": api_key.id,
                "key": raw_key,  # Only returned on creation!
                "name": api_key.name,
                "description": api_key.description,
                "owner_email": api_key.owner_email,
                "rate_limit_per_minute": api_key.rate_limit_per_minute,
                "rate_limit_per_day": api_key.rate_limit_per_day,
                "is_active": api_key.is_active,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
            }

        if session:
            return await _create(session)
        async with db.session() as s:
            return await _create(s)

    async def get_by_key(
        self,
        key: str,
        session: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Get API key details by the key value.

        Args:
            key: The API key string
            session: Optional existing database session

        Returns:
            Dict with key details (excluding the raw key) or None
        """
        async def _get(s: AsyncSession) -> dict[str, Any] | None:
            query = select(ApiKey).where(ApiKey.key == key)
            result = await s.execute(query)
            api_key = result.scalar_one_or_none()

            if api_key:
                return self._to_dict(api_key)
            return None

        if session:
            return await _get(session)
        async with db.session() as s:
            return await _get(s)

    async def get_by_id(
        self,
        key_id: int,
        session: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """Get API key by ID."""
        async def _get(s: AsyncSession) -> dict[str, Any] | None:
            query = select(ApiKey).where(ApiKey.id == key_id)
            result = await s.execute(query)
            api_key = result.scalar_one_or_none()

            if api_key:
                return self._to_dict(api_key)
            return None

        if session:
            return await _get(session)
        async with db.session() as s:
            return await _get(s)

    async def list_all(
        self,
        include_inactive: bool = False,
        session: AsyncSession | None = None,
    ) -> list[dict[str, Any]]:
        """
        List all API keys.

        Args:
            include_inactive: Whether to include deactivated keys
            session: Optional existing database session

        Returns:
            List of API key dicts
        """
        async def _list(s: AsyncSession) -> list[dict[str, Any]]:
            query = select(ApiKey)
            if not include_inactive:
                query = query.where(ApiKey.is_active)
            query = query.order_by(ApiKey.created_at.desc())

            result = await s.execute(query)
            keys = result.scalars().all()

            return [self._to_dict(k) for k in keys]

        if session:
            return await _list(session)
        async with db.session() as s:
            return await _list(s)

    async def validate(
        self,
        key: str,
        session: AsyncSession | None = None,
    ) -> tuple[bool, dict[str, Any] | None]:
        """
        Validate an API key and return its details if valid.

        Args:
            key: The API key to validate
            session: Optional existing database session

        Returns:
            Tuple of (is_valid, key_details or None)
        """
        async def _validate(s: AsyncSession) -> tuple[bool, dict[str, Any] | None]:
            query = select(ApiKey).where(ApiKey.key == key)
            result = await s.execute(query)
            api_key = result.scalar_one_or_none()

            if not api_key:
                return False, None

            if not api_key.is_valid():
                return False, self._to_dict(api_key)

            return True, self._to_dict(api_key)

        if session:
            return await _validate(session)
        async with db.session() as s:
            return await _validate(s)

    async def record_usage(
        self,
        key: str,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Record a usage of the API key.

        Args:
            key: The API key
            session: Optional existing database session

        Returns:
            True if successful
        """
        async def _record(s: AsyncSession) -> bool:
            query = (
                update(ApiKey)
                .where(ApiKey.key == key)
                .values(
                    last_used_at=datetime.now(UTC),
                    total_requests=ApiKey.total_requests + 1,
                )
            )
            result = await s.execute(query)
            return result.rowcount > 0

        if session:
            return await _record(session)
        async with db.session() as s:
            return await _record(s)

    async def update(
        self,
        key_id: int,
        name: str | None = None,
        description: str | None = None,
        rate_limit_per_minute: int | None = None,
        rate_limit_per_day: int | None = None,
        is_active: bool | None = None,
        expires_at: datetime | None = None,
        session: AsyncSession | None = None,
    ) -> dict[str, Any] | None:
        """
        Update an API key's settings.

        Args:
            key_id: ID of the key to update
            Other args: Fields to update (None = no change)
            session: Optional existing database session

        Returns:
            Updated key details or None if not found
        """
        async def _update(s: AsyncSession) -> dict[str, Any] | None:
            # Build update values
            values = {}
            if name is not None:
                values["name"] = name
            if description is not None:
                values["description"] = description
            if rate_limit_per_minute is not None:
                values["rate_limit_per_minute"] = rate_limit_per_minute
            if rate_limit_per_day is not None:
                values["rate_limit_per_day"] = rate_limit_per_day
            if is_active is not None:
                values["is_active"] = is_active
            if expires_at is not None:
                values["expires_at"] = expires_at

            if not values:
                # Nothing to update, just return current state
                return await self.get_by_id(key_id, s)

            values["updated_at"] = datetime.now(UTC)

            query = (
                update(ApiKey)
                .where(ApiKey.id == key_id)
                .values(**values)
            )
            await s.execute(query)

            logger.info(f"Updated API key id={key_id}")
            return await self.get_by_id(key_id, s)

        if session:
            return await _update(session)
        async with db.session() as s:
            return await _update(s)

    async def deactivate(
        self,
        key_id: int,
        session: AsyncSession | None = None,
    ) -> bool:
        """Deactivate an API key."""
        result = await self.update(key_id, is_active=False, session=session)
        return result is not None

    async def delete(
        self,
        key_id: int,
        session: AsyncSession | None = None,
    ) -> bool:
        """
        Permanently delete an API key.

        Args:
            key_id: ID of the key to delete
            session: Optional existing database session

        Returns:
            True if deleted
        """
        async def _delete(s: AsyncSession) -> bool:
            query = delete(ApiKey).where(ApiKey.id == key_id)
            result = await s.execute(query)

            if result.rowcount > 0:
                logger.info(f"Deleted API key id={key_id}")
                return True
            return False

        if session:
            return await _delete(session)
        async with db.session() as s:
            return await _delete(s)

    async def get_stats(
        self,
        session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Get API key statistics."""
        async def _stats(s: AsyncSession) -> dict[str, Any]:
            # Get all keys
            result = await s.execute(select(ApiKey))
            keys = result.scalars().all()

            total = len(keys)
            active = sum(1 for k in keys if k.is_active)
            expired = sum(1 for k in keys if k.expires_at and datetime.now(UTC) > k.expires_at)
            total_requests = sum(k.total_requests for k in keys)

            return {
                "total_keys": total,
                "active_keys": active,
                "inactive_keys": total - active,
                "expired_keys": expired,
                "total_requests": total_requests,
            }

        if session:
            return await _stats(session)
        async with db.session() as s:
            return await _stats(s)

    def _to_dict(self, api_key: ApiKey) -> dict[str, Any]:
        """Convert ApiKey model to dict (without exposing the key)."""
        return {
            "id": api_key.id,
            "key_prefix": api_key.key[:12] + "...",  # Only show prefix
            "name": api_key.name,
            "description": api_key.description,
            "owner_email": api_key.owner_email,
            "rate_limit_per_minute": api_key.rate_limit_per_minute,
            "rate_limit_per_day": api_key.rate_limit_per_day,
            "is_active": api_key.is_active,
            "is_valid": api_key.is_valid(),
            "last_used_at": api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            "total_requests": api_key.total_requests,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
            "updated_at": api_key.updated_at.isoformat() if api_key.updated_at else None,
        }


# Global repository instance
api_keys_repository = ApiKeysRepository()

