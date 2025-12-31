"""Database connection and session management."""

import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def is_configured(self) -> bool:
        """Check if database is configured."""
        return bool(settings.DATABASE_URL)

    def init(self) -> None:
        """Initialize the database engine and session factory."""
        if not self.is_configured:
            return

        # Convert standard postgres:// URL to asyncpg format
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

        # Remove sslmode from URL (asyncpg handles SSL differently)
        if "?" in db_url:
            base_url, params = db_url.split("?", 1)
            # Filter out sslmode and channel_binding params
            filtered_params = "&".join(
                p for p in params.split("&")
                if not p.startswith("sslmode=") and not p.startswith("channel_binding=")
            )
            db_url = f"{base_url}?{filtered_params}" if filtered_params else base_url

        # Configure SSL for Neon/Supabase connections
        connect_args: dict[str, Any] = {}
        if "neon.tech" in db_url or "supabase" in db_url:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ssl_context

        self._engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args=connect_args,
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def close(self) -> None:
        """Close the database engine."""
        if self._engine:
            await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self._session_factory:
            raise RuntimeError("Database not initialized. Call init() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global database manager instance
db = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with db.session() as session:
        yield session

